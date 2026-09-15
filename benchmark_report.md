# Benchmark Results - Test 3: High-FPS JPEG Performance Matrix

This report details PC-side JPEG encoding latency, frame sizes, and estimated network bandwidth requirements across resolution and quality profiles for stock Nintendo Switch Lite streaming.

## Performance Summary Matrix

| Resolution | Quality | Avg Encode (ms) | 95th % (ms) | Max Server FPS | Frame Size (KB) | 15 FPS (Mbps) | 30 FPS (Mbps) | 60 FPS (Mbps) |
|------------|---------|-----------------|-------------|----------------|-----------------|---------------|---------------|---------------|
| 360p (640x360) | 30% | 0.48 ms | 0.74 ms | 2100.7 FPS | 9.5 KB | 1.11 Mbps | 2.23 Mbps | 4.45 Mbps |
| 360p (640x360) | 50% | 0.48 ms | 0.71 ms | 2071.3 FPS | 10.8 KB | 1.27 Mbps | 2.54 Mbps | 5.08 Mbps |
| 360p (640x360) | 75% | 0.53 ms | 0.82 ms | 1871.7 FPS | 13.2 KB | 1.54 Mbps | 3.08 Mbps | 6.17 Mbps |
| 480p (854x480) | 30% | 0.84 ms | 1.15 ms | 1191.3 FPS | 13.9 KB | 1.63 Mbps | 3.26 Mbps | 6.52 Mbps |
| 480p (854x480) | 50% | 0.86 ms | 1.29 ms | 1157.6 FPS | 15.7 KB | 1.84 Mbps | 3.68 Mbps | 7.37 Mbps |
| 480p (854x480) | 75% | 0.86 ms | 1.23 ms | 1167.8 FPS | 18.6 KB | 2.18 Mbps | 4.35 Mbps | 8.71 Mbps |
| 720p (1280x720) | 30% | 1.83 ms | 2.39 ms | 547.9 FPS | 24.9 KB | 2.92 Mbps | 5.83 Mbps | 11.67 Mbps |
| 720p (1280x720) | 50% | 1.8 ms | 2.24 ms | 554.2 FPS | 27.5 KB | 3.22 Mbps | 6.43 Mbps | 12.87 Mbps |
| 720p (1280x720) | 75% | 1.85 ms | 2.43 ms | 539.6 FPS | 31.6 KB | 3.7 Mbps | 7.4 Mbps | 14.79 Mbps |

## Key Findings & Recommendations for Switch Lite Browser

- **360p @ 30 FPS (Q:50%)**: Lowest latency (~3-5 Mbps bandwidth), ideal for initial latency testing.
- **720p @ 30 FPS (Q:50%)**: Native Nintendo Switch Lite display resolution (~12-18 Mbps bandwidth), primary target for game streaming.
- **720p @ 60 FPS (Q:30%-50%)**: Requires high Wi-Fi bandwidth (~25-35 Mbps). Recommended for low-latency Wi-Fi networks.
