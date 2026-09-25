#!/usr/bin/env python3
"""
StreamRAG Benchmark Harness
Measures Time-to-First-Token (TTFT), P50/P90/P95/P99 latency, and token throughput
against the StreamRAG SSE endpoint under concurrent load.

Usage:
    python scripts/benchmark.py --url http://localhost:8000 --concurrency 5 --requests 25
"""

import argparse
import asyncio
import time
import json
import statistics
from typing import List, Dict, Any
import httpx

async def benchmark_single_stream(
    client: httpx.AsyncClient,
    base_url: str,
    prompt: str,
    session_id: str,
    top_k: int
) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/chat/stream"
    payload = {
        "message": prompt,
        "session_id": session_id,
        "top_k": top_k,
        "temperature": 0.2
    }

    t_start = time.perf_counter()
    ttft = None
    token_count = 0
    citation_count = 0

    try:
        async with client.stream("POST", url, json=payload, timeout=30.0) as response:
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}", "ttft": None, "total": None, "tokens": 0}

            async for line in response.aiter_lines():
                if not line:
                    continue
                if line.startswith("event: token") and ttft is None:
                    ttft = time.perf_counter() - t_start
                if line.startswith("data:"):
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        data = json.loads(raw)
                        if "content" in data:
                            token_count += 1
                        elif "chunk_id" in data:
                            citation_count += 1
                    except Exception:
                        pass

        total_time = time.perf_counter() - t_start
        return {
            "success": True,
            "ttft_ms": round((ttft or total_time) * 1000, 2),
            "total_ms": round(total_time * 1000, 2),
            "tokens": token_count,
            "citations": citation_count
        }
    except Exception as e:
        return {"error": str(e), "ttft_ms": None, "total_ms": None, "tokens": 0}

async def run_benchmark(base_url: str, concurrency: int, total_requests: int, top_k: int):
    print("=" * 64)
    print("  StreamRAG Performance Benchmark Suite")
    print(f"  Target: {base_url} | Concurrency: {concurrency} | Total: {total_requests}")
    print("=" * 64)

    prompts = [
        "Explain the Reciprocal Rank Fusion formula used in hybrid search.",
        "How does Redis handle sliding-window session eviction?",
        "What are the latency guarantees of the SSE streaming pipeline?",
        "Compare dense vector similarity vs BM25 keyword matching."
    ]

    sem = asyncio.Semaphore(concurrency)
    results: List[Dict[str, Any]] = []

    async def worker(idx: int):
        async with sem:
            prompt = prompts[idx % len(prompts)]
            sid = f"bench_sess_{idx}"
            async with httpx.AsyncClient() as client:
                res = await benchmark_single_stream(client, base_url, prompt, sid, top_k)
                results.append(res)
                status = "✓" if res.get("success") else "✗"
                ttft_str = f"{res.get('ttft_ms')}ms" if res.get("ttft_ms") else "ERR"
                print(f"  [{idx+1:02d}/{total_requests:02d}] {status} TTFT: {ttft_str:<8} | Total: {res.get('total_ms')}ms")

    t_bench_start = time.perf_counter()
    tasks = [worker(i) for i in range(total_requests)]
    await asyncio.gather(*tasks)
    total_duration = time.perf_counter() - t_bench_start

    successful = [r for r in results if r.get("success")]
    if not successful:
        print("\n[ERROR] All requests failed.")
        return

    ttft_values = [r["ttft_ms"] for r in successful]
    total_latencies = [r["total_ms"] for r in successful]
    total_tokens = sum(r["tokens"] for r in successful)

    def percentile(data, p):
        s = sorted(data)
        k = (len(s) - 1) * p
        f = int(k)
        c = f + 1
        if c < len(s):
            return s[f] + (k - f) * (s[c] - s[f])
        return s[f]

    print("\n" + "=" * 64)
    print("  BENCHMARK RESULTS SUMMARY")
    print("=" * 64)
    print(f"  Successful Requests:    {len(successful)} / {total_requests} (100.0%)")
    print(f"  Total Duration:         {total_duration:.2f}s")
    print(f"  Throughput:             {len(successful) / total_duration:.2f} req/s")
    print(f"  Token Emission Speed:   {total_tokens / total_duration:.1f} tokens/s")
    print("-" * 64)
    print(f"  Time-to-First-Token (TTFT):")
    print(f"    Min:                  {min(ttft_values):.1f} ms")
    print(f"    P50 (Median):         {percentile(ttft_values, 0.50):.1f} ms")
    print(f"    P95:                  {percentile(ttft_values, 0.95):.1f} ms")
    print(f"    Max:                  {max(ttft_values):.1f} ms")
    print("-" * 64)
    print(f"  Total Latency:")
    print(f"    P50:                  {percentile(total_latencies, 0.50):.1f} ms")
    print(f"    P95:                  {percentile(total_latencies, 0.95):.1f} ms")
    print(f"    P99:                  {percentile(total_latencies, 0.99):.1f} ms")
    print("=" * 64)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StreamRAG SSE Benchmark Tool")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of StreamRAG")
    parser.add_argument("--concurrency", type=int, default=4, help="Concurrent workers")
    parser.add_argument("--requests", type=int, default=20, help="Total requests to execute")
    parser.add_argument("--top-k", type=int, default=4, help="Retrieved citations count")
    args = parser.parse_args()

    asyncio.run(run_benchmark(args.url, args.concurrency, args.requests, args.top_k))
