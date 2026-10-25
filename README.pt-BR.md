# Agent Boundary Bench

Laboratório reproduzível para investigar o custo de cruzar fronteiras de processo e protocolo. A família de delegação compara Python em processo, HTTP convencional e A2A 1.0 JSON-RPC. A família de acesso a ferramentas compara MCP v2 em processo, stdio e Streamable HTTP. Todas executam o mesmo kernel determinístico de crédito corporativo sintético.

[README completo em inglês](README.md) · [Metodologia](docs/METHODOLOGY.md) · [Compatibilidade](docs/COMPATIBILITY.md) · [Validação realizada](VALIDATION.md)

Não usa LLM, dados financeiros reais, chaves comerciais ou banco de dados. A v0.2.0 inclui tools/resources MCP, fan-out/fan-in limitado e amplificação controlada de contexto e chamadas. Os papéis de especialistas continuam sintéticos; o laboratório não mede automaticamente autonomia de agentes nem benefícios de isolamento sob falha.

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

Os três especialistas compartilham as regras. O supervisor valida cada resposta contra o resultado determinístico esperado. Os casos têm corpo canônico de exatamente 1, 16 ou 128 KiB; os envelopes aumentam o tamanho efetivamente transferido. Esperas assíncronas de 50 e 250 ms simulam espera de I/O, **não trabalho de CPU**.

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
```

As matrizes `full.json` e `mcp-full.json` contêm 1.620 rodadas cada; só as janelas de medição somam 13,5 horas por matriz. A campanha MCP de amplificação contém 1.440 rodadas e separa payload, cópias de contexto, repetições de tools/resources e fan-out da variação de taxa. Comece por `mcp-smoke.json` ou pelo piloto MCP de cinco repetições.

```bash
uv run abb run --scenario mcp-streamable-http --payload-bytes 16384 \
  --context-copies 4 --tool-repetitions 2 --resource-reads 2 \
  --specialist-repetitions 4 --parallel --fanout-limit 8
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

HTTP, A2A e MCP Streamable HTTP usam a mesma imagem e limites. O A2A anuncia o endereço interno `a2a:8100`; o MCP atende em `mcp:8100/mcp`. `verify` acessa os três serviços com seus clientes públicos e compara o resultado de negócio. O harness nativo usa subprocessos, não esses containers.

Para k6, execute `uv run abb gateway --scenario a2a` em um terminal e, em outro, `ABB_RATE=20 ABB_DURATION=10s k6 run k6/arrival.js`. A configuração usa chegadas constantes independentes das respostas. Essa medição acrescenta uma entrada HTTP uniforme no supervisor; não misture seus números com os do harness nativo. O README em inglês mostra a gravação dos dados brutos do k6.

## O que os resultados permitem afirmar

O manifesto registra commit, ambiente, restrições de recursos, versões, seed, workload e estado da instrumentação. Os dados preservam erros, timeouts, descartes, atraso do gerador, bytes e chamadas. O relatório verifica hashes e contagens antes de calcular estatísticas. P99 de smoke tests tem pouca sustentação amostral; não é evidência de capacidade ou saturação.

A telemetria usa OpenTelemetry, contexto W3C e exportação local de metadados. Seu custo inclui a exportação síncrona. Payloads não são registrados nos spans. Dados ausentes continuam nulos; o relatório não inventa amostras nem decompõe causalmente a rede subtraindo médias.

**MCP e A2A têm responsabilidades diferentes:** A2A delega tarefas a agentes; MCP permite acesso a ferramentas, recursos e prompts. A v0.2 implementa MCP em uma família experimental separada. Uma diferença de latência entre essas famílias não demonstra que um protocolo substitui o outro.

Nos cenários HTTP/A2A, bytes representam corpos HTTP observados. Nos cenários MCP, representam argumentos/resultados de tool e URI/conteúdo de resource, excluindo framing JSON-RPC/HTTP. `context_bytes`, `tool_calls` e `resource_reads` registram a amplificação explicitamente; definições diferentes não devem ser agregadas sem ressalva.

## Architectural Decision Insights

O objetivo é subsidiar decisões entre monólito modular, serviços e topologias híbridas. Uma fronteira pode ter custo relevante para chamadas pequenas e ainda atender a requisitos de interoperabilidade ou implantação independente. Este ambiente não mede esses benefícios automaticamente: eles exigem experimentos próprios. Não há vencedor previamente definido.

Base escolhida: `codex-python-engineering-harness`, perfil `service`, preservando arquitetura, verificação e proveniência. Consulte os [ADRs](docs/adr/), o [roadmap](docs/ROADMAP.md) e as [regras de contribuição](CONTRIBUTING.md). O projeto permanece privado até autorização para publicação.
