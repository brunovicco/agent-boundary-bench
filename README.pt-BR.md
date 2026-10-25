# Agent Boundary Bench

Laboratório reproduzível para investigar quanto custa transformar uma chamada local entre especialistas em delegação distribuída. Compara Python em processo, HTTP convencional e A2A 1.0 JSON-RPC com o SDK oficial, executando o mesmo kernel determinístico de crédito corporativo sintético.

[README completo em inglês](README.md) · [Metodologia](docs/METHODOLOGY.md) · [Compatibilidade](docs/COMPATIBILITY.md) · [Validação realizada](VALIDATION.md)

Não usa LLM, dados financeiros reais, chaves comerciais ou banco de dados. Os papéis de especialistas são sintéticos; a v0.1 não mede autonomia de agentes nem benefícios de isolamento sob falha.

| Cenário | Fronteira | Especialista remoto |
|---|---|---|
| A0 `local` | Interface Python tipada | Nenhum |
| A1 `http` | JSON e HTTP/1.1 persistente | Um processo, um worker |
| A2 `a2a` | A2A JSON-RPC e SDK oficial | Um processo, um worker |

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
uv run abb report --input results/ --output reports/latest
```

Os subprocessos remotos são iniciados e encerrados pelo comando `run`. O cenário local funciona sem serviços externos. Após instalar dependências, os workloads básicos funcionam offline.

```bash
uv run abb run --scenario a2a --payload-bytes 131072 --wait-ms 250 \
  --parallel --telemetry --rate 20 --duration 10
uv run abb campaign --config experiments/pilot.json --output results/pilot
uv run abb campaign --config experiments/full.json --output results/full
```

A matriz completa contém 1.620 rodadas: cinco repetições, 5/20/50 RPS, três payloads, três workloads, modos sequencial/paralelo e telemetria desligada/ligada. Só as janelas de medição somam 13,5 horas. Faça o piloto e calibre a carga primeiro. A ordem é randomizada de maneira reproduzível por seed. Rodadas incompletas não recebem manifesto de conclusão.

## Docker e k6

```bash
docker compose up --build --wait
uv run abb health --url http://127.0.0.1:8101
uv run abb health --url http://127.0.0.1:8102
docker compose --profile tools run --rm verify
docker compose down --remove-orphans
```

Os serviços têm a mesma imagem e limites. O A2A anuncia o endereço interno `a2a:8100`; `verify` acessa os dois serviços na rede do Compose. O harness nativo usa subprocessos, não esses containers. Consulte `VALIDATION.md` antes de afirmar que Docker ou CI foram executados.

Para k6, execute `uv run abb gateway --scenario a2a` em um terminal e, em outro, `ABB_RATE=20 ABB_DURATION=10s k6 run k6/arrival.js`. A configuração usa chegadas constantes independentes das respostas. Essa medição acrescenta uma entrada HTTP uniforme no supervisor; não misture seus números com os do harness nativo. O README em inglês mostra a gravação dos dados brutos do k6.

## O que os resultados permitem afirmar

O manifesto registra commit, ambiente, restrições de recursos, versões, seed, workload e estado da instrumentação. Os dados preservam erros, timeouts, descartes, atraso do gerador, bytes e chamadas. O relatório verifica hashes e contagens antes de calcular estatísticas. P99 de smoke tests tem pouca sustentação amostral; não é evidência de capacidade ou saturação.

A telemetria usa OpenTelemetry, contexto W3C e exportação local de metadados. Seu custo inclui a exportação síncrona. Payloads não são registrados nos spans. Dados ausentes continuam nulos; o relatório não inventa amostras nem decompõe causalmente a rede subtraindo médias.

**MCP e A2A têm responsabilidades diferentes:** A2A delega tarefas a agentes; MCP permite acesso a ferramentas, recursos e prompts. O SDK MCP v2 foi pesquisado e fica para experimentos separados na v0.2.

## Architectural Decision Insights

O objetivo é subsidiar decisões entre monólito modular, serviços e topologias híbridas. Uma fronteira pode ter custo relevante para chamadas pequenas e ainda atender a requisitos de interoperabilidade ou implantação independente. Este ambiente não mede esses benefícios automaticamente: eles exigem experimentos próprios. Não há vencedor previamente definido.

Base escolhida: `codex-python-engineering-harness`, perfil `service`, preservando arquitetura, verificação e proveniência. Consulte os [ADRs](docs/adr/), o [roadmap](docs/ROADMAP.md) e as [regras de contribuição](CONTRIBUTING.md). O projeto permanece privado até autorização para publicação.
