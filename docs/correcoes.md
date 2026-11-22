# Correções desta versão

Percentuais e contagens dos erros foram medidos na última base gerada pela versão original.

## Erros que mudavam os números

| Problema | Efeito | Correção |
|---|---|---|
| Custo estimado como 60% do preço, ignorando o custo do cadastro | Na base original, lucro de R$ 1,12 milhão em vez de R$ 1,39 milhão e margem de 36,4% em vez de 45,3% | Custo = quantidade × custo do produto |
| Receita e lucro preenchidos em pedido cancelado ou devolvido | Somar a fato sem filtro inflava o resultado | Métricas zeradas nesses pedidos e valor original em `order_value` |
| 73% dos eventos fora da vigência da campanha | Atribuição a campanhas que não estavam no ar | Gerador corrigido e regra na Silver |
| 299 de 2.000 pedidos anteriores ao cadastro do cliente | Histórico impossível | Gerador corrigido e regra na Silver |
| Gerador criava 16 das 20 subcategorias | Esportes com 5 produtos, as outras categorias com 25 | 20 produtos por categoria |
| Top 10 agrupado pelo nome do produto | Produtos homônimos eram somados | Agrupamento pela chave |
| Cidade sorteada sem relação com o estado | Geografia incoerente | Cidades por estado |

## Confiabilidade

| Problema | Efeito | Correção |
|---|---|---|
| Seed incompleta e datas relativas a hoje | Cada execução gerava dados diferentes | Seed em todo sorteio e período fixo |
| Bronze relia e regravava os arquivos com colunas extras | Não era cópia fiel da fonte | Cópia byte a byte, com controle nos metadados |
| Silver convertia tipos antes de validar | Um valor vazio derrubava o pipeline | Validação com rejeição registrada |
| Linhas descartadas sem registro | Perda invisível | Arquivo de rejeições com motivo |
| `gold.db` apagado antes da recriação | Uma falha deixava o Superset sem banco | Troca do arquivo só no fim |
| Scripts dependiam da pasta atual | Falhavam fora da raiz | Caminhos absolutos e `run.py` |
| Nomes de meses dependiam do idioma da máquina | Resultado variava por ambiente | Nomes fixos em português |
| Nenhum teste | Erros passavam despercebidos | Testes automatizados com pytest |

## Infraestrutura e segurança

| Problema | Efeito | Correção |
|---|---|---|
| A imagem do MinIO usada não pôde mais ser baixada | Um clone novo não subia | RustFS 1.0.4, fixado por digest |
| Superset com debugger, aberto à rede | Risco de execução remota de código | Servidor gunicorn, portas só em `127.0.0.1` |
| Senhas e chave secreta no código | Credenciais públicas | `.env` aleatório, fora do git |
| DuckDB sem versão fixa no Superset | Podia divergir do pipeline que gera o arquivo | Mesma versão nos dois, garantida por teste |
| Dashboard só no volume Docker de uma máquina | Não existia para quem clonasse | Exportado, versionado e importado ao subir |

## Documentação e análise

| Problema | Correção |
|---|---|
| README omitia a etapa 05 e conectava o Superset a um banco em memória | Passo a passo refeito e testado |
| Script com 9 consultas e documentação com 11, em cópias divergentes | Um arquivo por consulta em `sql/`, usado em todo lugar |
| Faixa de desconto saía como `0%%` | Corrigido |
| "ROI" e "conversão" em consultas que mediam receita | Nomes do que é realmente calculado |
| "LTV" para receita histórica | "Receita histórica por cliente" |
| Pedido sem atribuição chamado de "Orgânico" | "Sem campanha" |
| Conclusões causais sobre marketing e desconto | Limitações explícitas |
