import http from 'k6/http';
import { check } from 'k6';
import { Trend, Counter } from 'k6/metrics';

// Uniform supervisor ingress: keep separate from native harness latency.
const latency = new Trend('abb_measured_latency', true);
const completions = new Counter('abb_measured_completed');
const failures = new Counter('abb_measured_errors');
const base = __ENV.ABB_URL || 'http://127.0.0.1:8200';
export const options = {
  scenarios: {
    measured: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.ABB_RATE || 5),
      timeUnit: '1s',
      duration: __ENV.ABB_DURATION || '10s',
      preAllocatedVUs: Number(__ENV.ABB_VUS || 64),
      maxVUs: Number(__ENV.ABB_VUS || 64),
      gracefulStop: '10s',
    },
  },
  thresholds: {
    abb_measured_errors: ['count==0'],
    dropped_iterations: ['count==0'],
  },
};
export function setup() {
  for (let i = 0; i < 3; i++) {
    const r = http.post(`${base}/execute`, null, { timeout: '5s', tags: { phase: 'warmup' } });
    if (r.status !== 200) throw new Error('warmup failed');
  }
}
export default function () {
  const r = http.post(`${base}/execute`, null, { timeout: '5s' });
  const valid = check(r, {
    'valid business contract': (response) => response.status === 200 && response.json('results').length === 3,
  });
  latency.add(r.timings.duration);
  completions.add(1);
  failures.add(valid ? 0 : 1);
}
