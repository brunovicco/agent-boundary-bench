# Agent Boundary Bench

[![quality](https://github.com/brunovicco/agent-boundary-bench/actions/workflows/quality.yml/badge.svg)](https://github.com/brunovicco/agent-boundary-bench/actions/workflows/quality.yml)
[![release](https://img.shields.io/badge/release-v0.2.0-blue)](docs/RELEASE_0.2.0.md)
[![python](https://img.shields.io/badge/python-3.12--3.14-3776AB)](pyproject.toml)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Laboratório reproduzível para investigar o custo de cruzar fronteiras de processo e protocolo. A família de delegação compara Python em processo, HTTP convencional e A2A 1.0 JSON-RPC. A família de acesso a ferramentas compara MCP v2 em processo, stdio e Streamable HTTP. Todas executam o mesmo kernel determinístico de crédito corporativo sintético.

[README completo em inglês](README.md) · [Notas da v0.2.0](docs/RELEASE_0.2.0.md) · [Resiliência v0.3](docs/RESILIENCE.md) · [Isolamento de recursos v0.3](docs/RESOURCE_ISOLATION.md) · [Metodologia](docs/METHODOLOGY.md) · [Compatibilidade](docs/COMPATIBILITY.md) · [Validação realizada](VALIDATION.md)

Não usa LLM, dados financeiros reais, chaves comerciais ou banco de dados. A versão atual, v0.2.0, inclui tools/resources MCP, fan-out/fan-in limitado e amplificação controlada de contexto e chamadas. Os papéis de especialistas continuam sintéticos; o laboratório não mede automaticamente autonomia de agentes nem benefícios de isolamento sob falha.

A linha `0.3.0.dev0` implementa falhas controladas na delegação, retries limitados, IDs
idempotentes e backpressure no serviço. O milestone de isolamento adiciona tratamento em
containers, trabalho sintético fixo de CPU/memória e evidência observada de cgroup v2. Isso ainda não
representa uma release v0.3 nem evidência de capacidade sustentada.

| Cenário | Fronteira | Especialista remoto |
|---|---|---|
| A0 `local` | Interface Python tipada | Nenhum |
| A1 `http` | JSON e HTTP/1.1 persistente | Um processo, um worker |
| A2 `a2a` | A2A JSON-RPC e SDK oficial | Um processo, um worker |

Os cenários MCP respondem a outra pergunta experimental:

| Cenário | Fronteira de acesso a ferramentas | Processo adicional |
|---|---|---|
| T0 `mcp-inprocess` | Dispatcher direto do SDK oficial | Não |
| T1 `mcp-stdio` | MCP JSON-RPC por stdin/stdout | Um processo filho |
| T2 `mcp-streamable-http` | MCP Streamable HTTP | Um processo, um worker |

Os três especialistas compartilham as regras. O supervisor valida cada resposta contra o resultado determinístico esperado. Os casos têm corpo canônico de exatamente 1, 16 ou 128 KiB; os envelopes aumentam o tamanho efetivamente transferido. Esperas assíncronas de 50 e 250 ms simulam espera de I/O, **não trabalho de CPU**. `cpu_iterations` e `memory_bytes` são workloads sintéticos fixos e separados; não são inferência nem duração calibrada.

## Executar

Requer Python 3.12+ e uv. Execute na raiz do projeto:

```bash
uv sync --frozen --all-groups
uv run abb validate
uv run python scripts/quality_gate.py
uv run abb run --scenario local --profile smoke
uv run abb run --scenario http --profile smoke
uv run abb run --scenario a2a --profile smoke
uv run abb run --scenario mcp-inprocess --profile smoke
uv run abb run --scenario mcp-stdio --profile smoke
uv run abb run --scenario mcp-streamable-http --profile smoke
uv run abb report --input results/ --output reports/latest
```

Os subprocessos remotos são iniciados e encerrados pelo comando `run`. O cenário local funciona sem serviços externos. Após instalar dependências, os workloads básicos funcionam offline.

```bash
uv run abb run --scenario a2a --payload-bytes 131072 --wait-ms 250 \
  --parallel --telemetry --rate 20 --duration 10
uv run abb campaign --config experiments/pilot.json --output results/pilot
uv run abb campaign --config experiments/full.json --output results/full
uv run abb campaign --config experiments/mcp-pilot.json --output results/mcp-pilot
uv run abb campaign --config experiments/mcp-full.json --output results/mcp-full
uv run abb campaign --config experiments/mcp-amplification-full.json \
  --output results/mcp-amplification
uv run abb campaign --config experiments/resilience-smoke.json \
  --output results/resilience-smoke
uv run abb campaign --config experiments/timeout-smoke.json \
  --output results/timeout-smoke
uv run abb campaign --config experiments/backpressure-smoke.json \
  --output results/backpressure-smoke
```

As matrizes `full.json` e `mcp-full.json` contêm 1.620 rodadas cada; só as janelas de medição somam 13,5 horas por matriz. A campanha MCP de amplificação contém 1.440 rodadas e separa payload, cópias de contexto, repetições de tools/resources e fan-out da variação de taxa. Comece por `mcp-smoke.json` ou pelo piloto MCP de cinco repetições.

```bash
uv run abb run --scenario mcp-streamable-http --payload-bytes 16384 \
  --context-copies 4 --tool-repetitions 2 --resource-reads 2 \
  --specialist-repetitions 4 --parallel --fanout-limit 8
```

Exemplo de recuperação controlada em desenvolvimento:

```bash
uv run abb run --scenario a2a --profile smoke \
  --fault-mode after-commit --max-attempts 2 --attempt-timeout 1 \
  --idempotency --output results/v030-a2a-after-commit
```

O schema v3 registra tentativas, retries, execuções do kernel, hits idempotentes, falhas
injetadas, rejeições e tempo de espera por admissão. Consulte
[RESILIENCE.md](docs/RESILIENCE.md) antes de interpretar esses campos.

Smoke nativo do workload de recursos, sem alegar isolamento por container:

```bash
uv run abb run --scenario a2a --profile smoke --wait-ms 50 \
  --cpu-iterations 25000 --memory-bytes 8388608 \
  --output results/cpu-work-native-smoke
```

## Docker e k6

```bash
docker compose up --build --wait
uv run abb health --url http://127.0.0.1:8101
uv run abb health --url http://127.0.0.1:8102
uv run abb health --url http://127.0.0.1:8103
docker compose --profile tools run --rm verify
docker compose down --remove-orphans
```

HTTP, A2A e MCP Streamable HTTP usam a mesma imagem e limites. O A2A anuncia o endereço interno `a2a:8100`; o MCP atende em `mcp:8100/mcp`. `verify` acessa os três serviços com seus clientes públicos e compara o resultado de negócio. Build, health checks e equivalência funcional do Compose foram validados no macOS; o GitHub Actions executa a mesma topologia funcional sem publicar tempos de runners compartilhados. O harness nativo usa subprocessos, não esses containers.

O overlay opcional `compose.isolation.yaml` executa o harness em container e usa cgroups
separados e configuráveis para HTTP/A2A. O schema v4 registra os limites e contadores cgroup v2
realmente observados; o nome do perfil, sozinho, não comprova isolamento. Os comandos de smoke e
campanha completa estão em [RESOURCE_ISOLATION.md](docs/RESOURCE_ISOLATION.md).

Para k6, execute `uv run abb gateway --scenario a2a` em um terminal e, em outro, `ABB_RATE=20 ABB_DURATION=10s k6 run k6/arrival.js`. A configuração usa chegadas constantes independentes das respostas. Essa medição acrescenta uma entrada HTTP uniforme no supervisor; não misture seus números com os do harness nativo. O README em inglês mostra a gravação dos dados brutos do k6.

## O que os resultados permitem afirmar

O manifesto registra commit, ambiente, restrições de recursos, versões, seed, workload e estado da instrumentação. Os dados preservam erros, timeouts, descartes, atraso do gerador, bytes e chamadas. O relatório verifica hashes e contagens antes de calcular estatísticas. P99 de smoke tests tem pouca sustentação amostral; não é evidência de capacidade ou saturação.

A telemetria usa OpenTelemetry, contexto W3C e exportação local de metadados. Seu custo inclui a exportação síncrona. Payloads não são registrados nos spans. Dados ausentes continuam nulos; o relatório não inventa amostras nem decompõe causalmente a rede subtraindo médias.

**MCP e A2A têm responsabilidades diferentes:** A2A delega tarefas a agentes; MCP permite acesso a ferramentas, recursos e prompts. A v0.2 implementa MCP em uma família experimental separada. Uma diferença de latência entre essas famílias não demonstra que um protocolo substitui o outro.

Nos cenários HTTP/A2A, bytes representam corpos HTTP observados. Nos cenários MCP, representam argumentos/resultados de tool e URI/conteúdo de resource, excluindo framing JSON-RPC/HTTP. `context_bytes`, `tool_calls` e `resource_reads` registram a amplificação explicitamente; definições diferentes não devem ser agregadas sem ressalva.

## Architectural Decision Insights

O objetivo é subsidiar decisões entre monólito modular, serviços e topologias híbridas. Uma fronteira pode ter custo relevante para chamadas pequenas e ainda atender a requisitos de interoperabilidade ou implantação independente. Este ambiente não mede esses benefícios automaticamente: eles exigem experimentos próprios. Não há vencedor previamente definido.

O piloto MCP real executou 120 rodadas e concluiu 1.200/1.200 requisições sem erros, timeouts ou descartes. Na condição sem telemetria, sem cópias de contexto e sem leituras de resources, a mediana dos P50 por rodada foi 3,110 ms para dispatch direto, 5,842 ms para stdio e 6,315 ms para Streamable HTTP (cinco rodadas, 50 amostras por fronteira). Duas leituras não cacheadas por especialista elevaram as medianas observadas nas três fronteiras. São resultados curtos em host compartilhado: validam o caminho experimental, mas não demonstram capacidade sustentada nem substituição entre MCP e A2A.

Base escolhida: `codex-python-engineering-harness`, perfil `service`, preservando arquitetura, verificação e proveniência. Consulte os [ADRs](docs/adr/), o [roadmap](docs/ROADMAP.md), as [notas da v0.2.0](docs/RELEASE_0.2.0.md), a [resiliência v0.3](docs/RESILIENCE.md), o [isolamento de recursos](docs/RESOURCE_ISOLATION.md) e as [regras de contribuição](CONTRIBUTING.md).

O repositório público canônico é [brunovicco/agent-boundary-bench](https://github.com/brunovicco/agent-boundary-bench). Bundles locais são apenas artefatos de recuperação e não substituem o remote Git oficial.
