# Verificações do fechamento

Conferido em 26/11/2026, horário de Belém, a partir de `git archive d27c89de` e somente a nova seleção. [Comandos, saídas e limites](verificacao_copia_limpa.json) e [hashes dos insumos históricos](verificacao_entradas.json). O caminho temporário registrado é evidência da verificação, não dependência de reprodução.

- Manifesto próprio fechado, lista exata e links locais: aprovados.
- Baseline histórica:89 hashes aprovados;46 evidências de VM herdadas verificadas pelo script existente, sem duplicação.
- Tabelas de auditoria: reconciliação de totais/classes, exclusões, percentuais e conflitos aprovada pelo verificador existente.
- Caso sintético: duplicatas, conflitos e IDs locais repetidos aprovados pelo `auditar_split.py sintetico` entregue.
- Métricas sintéticas do baseline: aprovadas;13 módulos importados da cópia limpa, sem depender de scripts no checkout original. Ambiente científico existente do lock reutilizado; não se instalou um novo ambiente neste fechamento.
- Candidato existente:12 matrizes/hash dos índices/normalizador conferidos; padronização float32 recomposta em todas as linhas, somente leitura. Inclui sexta apenas para as verificações de qualidade/representação, sem previsão nem métricas de desempenho.
- Reexportação em pasta temporária:81 parâmetros e colisões coincidem com as tabelas entregues (comparação de campos CSV após normalização dos finais de linha).
- VM:231 checks/tolerância zero preservados;12 matrizes,192 suportes/recalls nominais,20 estatísticas entre seeds e3 pares de orçamento recalculados da evidência entregue. AP é preservada dos ensaios; não se recalcula AP sem scores neste fechamento.
- Preparador de nova execução: destino novo, hash do ZIP e configuração de caminhos conferidos, sem instalação/treino. Única adaptação funcional no supervisor: `repo_estado` configurável para a consulta Git; cálculo numérico preservado.
- Sintaxe Python/Bash e inspeção por marcadores de credenciais: aprovadas. Logs já sanitizados são entregues sem ANSI/brancos finais; não há sockets SSH, chaves ou tokens na seleção.

As cópias editoriais usam LF e removem brancos finais. Os relatórios VM ganharam aviso e links relativos; nenhum resultado foi recalculado nessa edição. [PROVENIENCIA.json](PROVENIENCIA.json) guarda SHA da origem e da entrega. Os manifestos históricos foram preservados byte a byte em `historicos/`; eles descrevem o acervo original e não devem ser usados como manifesto desta seleção. O verificador confere também sua relação com os hashes originais do retorno VM.

Reproduzir a verificação documental, sem dataset:

```bash
python3 -B verificar.py
python3 -B verificar_auditoria.py fonte/auditoria_referencia
```

O relatório local da missão registra também a revisão dos caminhos indexados, `git diff --cached --check` e o SHA final do commit. A lista revisável é [LISTA_ARQUIVOS.txt](LISTA_ARQUIVOS.txt). Rodada experimental concluída permanece a única fonte do desempenho reportado.
