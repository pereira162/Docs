# **Contexto do Projeto e Diretrizes para Assistente de IA**

## **1\. Objetivo Principal**

O objetivo deste projeto é criar uma ferramenta, primariamente utilizando Docling, para **extrair, processar e salvar informações** de uma vasta gama de fontes e tipos de arquivo (documentos, imagens, sites, etc.).

O resultado final deve ser uma coleção de arquivos **organizados e em formato de fácil leitura para IA (como Markdown ou JSON)**, otimizados para uso em sistemas de RAG (Retrieval-Augmented Generation). A função primária é a extração e o download dos dados processados. A capacidade de fazer perguntas sobre os documentos é uma funcionalidade secundária.

## **2\. Critérios Essenciais (Regras Não Negociáveis)**

Estas são as diretrizes mais importantes. Todas as sugestões, códigos e respostas da IA devem segui-las rigorosamente.

* **Custo Zero:** A solução deve ser **100% gratuita**. Não utilize ou sugira serviços de nuvem pagos, APIs com custos, ou qualquer componente que tenha um limite baixo no plano gratuito e que possa levar a cobranças.  
* **Sem Limites de Uso:** O sistema não deve ter limite de armazenamento ou de número de arquivos. Para alcançar isso, o foco deve ser o uso de **recursos locais da máquina do usuário** (cache no disco, sistema de arquivos) para todo o armazenamento de dados.  
* **Foco na Extração e Formatação:** A prioridade é o fluxo:  
  1. Receber uma fonte (URL, caminho de arquivo).  
  2. Identificar o tipo de arquivo e usar a melhor ferramenta para **extrair o conteúdo bruto** (ex: OCR para imagens).  
  3. Limpar, formatar e "chunk" (dividir) o texto.  
  4. Salvar o resultado localmente em um formato estruturado (**Markdown ou JSON**), em uma estrutura de pastas organizada.  
* **Suporte Amplo a Arquivos:** A ferramenta deve ser capaz de processar os seguintes formatos:  
  * **Essenciais:** PDF, DOCX, Imagens (JPG, PNG, etc.), HTML (URLs).  
  * **Desejáveis (Explorar Soluções):** Vídeos, Planilhas (XLS, XLSX), Apresentações (PPT, PPTX).  
* **Tecnologia é um Meio, Não um Fim:** A stack tecnológica específica **não é importante**. A IA deve sugerir a solução mais **simples e direta** que cumpra os critérios acima, utilizando bibliotecas de código aberto e gratuitas.

## **3\. Sugestões de Ferramentas (Local-First)**

Para cumprir o critério de suporte a arquivos, a IA deve sugerir bibliotecas que rodem localmente:

* **PDF:** PyPDF2, pdfplumber (para extração mais robusta de tabelas e layout).  
* **DOCX:** python-docx.  
* **Imagens (OCR):** pytesseract (requer instalação do Tesseract OCR no sistema).  
* **Planilhas:** pandas, openpyxl.  
* **Apresentações:** python-pptx.  
* **Vídeos (Transcrição e Análise Visual):**  
  * **Áudio:** Whisper (executado localmente) ou Vosk para transcrever a fala.  
  * **Visual:** FFmpeg para extrair frames (imagens) do vídeo em intervalos. pytesseract para aplicar OCR nesses frames e extrair texto de slides, código, etc.

## **4\. Como o Assistente de IA Deve Atuar**

* **Pense "Local-First":** Sempre que precisar processar arquivos, sua primeira sugestão deve ser uma biblioteca que funcione offline.  
* **Simplicidade Acima de Tudo:** Evite arquiteturas complexas quando um script ou uma ferramenta dedicada como Docling for suficiente.  
* **Foque no Problema, Não na Ferramenta (além do Docling):** Concentre-se em resolver o problema funcional ("como extrair texto de um PPTX?") usando as bibliotecas mais simples e gratuitas disponíveis para, se necessário, complementar a ferramenta principal.  
* **Ignore o Histórico de Stacks Complexas:** Desconsidere discussões anteriores sobre stacks com FastAPI, Next.js, Qdrant Cloud, etc.

## **5\. Exemplos de Interação Ideal**

**Pergunta do Usuário:** "Como posso extrair o texto de uma imagem e salvá-lo em JSON?"

* **Resposta CORRETA (✅):** "Podemos usar a biblioteca pytesseract para fazer o OCR da imagem e extrair o texto. Depois, estruturamos essa saída em um arquivo JSON. O processo seria: 1\. Carregar a imagem com uma biblioteca como a Pillow. 2\. Passar a imagem para o pytesseract para obter o texto. 3\. Criar um dicionário Python com o texto e metadados (como o nome do arquivo) e salvá-lo como um arquivo JSON. Aqui está um exemplo de código..."

**Pergunta do Usuário:** "Como posso processar um vídeo para extrair o máximo de informação?"

* **Resposta CORRETA (✅):** "Para uma solução local e gratuita, podemos combinar duas estratégias: 1\. **Extrair o áudio** com FFmpeg e transcrevê-lo com Whisper para obter a fala. 2\. **Extrair frames visuais** com FFmpeg (ex: um a cada 10 segundos) e usar pytesseract para ler o texto de qualquer slide ou código na tela. O resultado final seria um arquivo .md que combina a transcrição com o conteúdo visual identificado em cada timestamp, criando um documento rico e pesquisável."