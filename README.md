# Vistoria-Patrimonial
Inspeção técnica detalhada que verifica, cataloga e documenta o estado de conservação, a existência e as condições físicas de bens móveis, imóveis e ativos de uma empresa ou pessoa física
# Vistoria Patrimonial — Protótipo de Portfólio

Aplicação demonstrativa para vistoria de patrimônio por QR Code. O projeto mostra como integrar uma interface Streamlit, um leitor de QR Code no navegador com `@zxing/browser`, consultas SQL em Python, registro das leituras, painel de acompanhamento e geração de relatórios PDF.

> **Aviso importante:** este repositório é um protótipo de portfólio, não um sistema pronto para uso administrativo ou institucional. Os dados são fictícios. O SQLite usado na demonstração não deve ser considerado persistente no Streamlit Community Cloud, e os dados podem ser perdidos.

## Funcionalidades da Versão 1

- Seleção do departamento e abertura de uma vistoria.
- Leitura de QR Code pela câmera do dispositivo, com autorização do usuário.
- Integração do leitor `@zxing/browser` por meio de um componente JavaScript incorporado ao Streamlit — sem redirecionar o usuário para um site externo de leitura.
- Consulta ao banco SQLite usando parâmetros SQL.
- Verificação de cadastro e departamento associado ao patrimônio.
- Registro de leituras e possíveis divergências.
- Cadastro demonstrativo de bens e departamentos.
- Geração de QR Codes em PNG para impressão.
- Painel de resultados e exportação de relatório PDF com ReportLab.
- Registros fictícios para facilitar a primeira demonstração.

## Fluxo da aplicação

1. O usuário seleciona o departamento e inicia a vistoria.
2. Clica em **Ligar câmera e ler QR**.
3. O componente JavaScript usa `@zxing/browser` para decodificar a etiqueta.
4. O texto do QR Code retorna ao Streamlit na mesma página.
5. Python consulta o SQLite, encontra o patrimônio e confere a qual departamento ele pertence.
6. A aplicação registra a leitura e mostra o resultado na tela.
7. O painel permite revisar as leituras e gerar um relatório PDF.

### Classificações demonstradas

- **Leitura confirmada:** o código existe e o bem está cadastrado no departamento vistoriado.
- **Identificação pendente:** o código lido não existe no cadastro.
- **Possível divergência:** o bem existe, mas está associado a outro departamento.

A ausência de leitura não prova que um bem esteja fisicamente ausente. O resultado deve ser entendido como **não localizado durante a vistoria**, exigindo conferência humana. A versão atual demonstra leitura de QR Code; não realiza reconhecimento por IA de fotografias.

## Tecnologias

- Python
- Streamlit
- SQLite
- JavaScript
- [`@zxing/browser`](https://github.com/zxing-js/browser)
- Pandas
- [`qrcode`](https://pypi.org/project/qrcode/)
- [`ReportLab`](https://www.reportlab.com/)

## Executar localmente para testar

Requer Python 3.10 ou superior recomendado.

```bash
git clone https://github.com/SEU-USUARIO/vistoria-patrimonial-v1.git
cd vistoria-patrimonial-v1

python -m venv .venv
```

Ative o ambiente virtual:

**Windows (PowerShell)**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux/macOS**

```bash
source .venv/bin/activate
```

Instale as dependências e inicie:

```bash
pip install -r requirements.txt
streamlit run app.py
```

O banco e alguns patrimônios fictícios são criados automaticamente na primeira execução. Para testar o leitor, abra a aplicação em um navegador com suporte à câmera e conceda a permissão solicitada. O acesso à câmera depende de contexto seguro (normalmente HTTPS ou localhost).

## Publicar no Streamlit Community Cloud

1. Crie um repositório GitHub e envie os arquivos deste projeto.
2. Entre no [Streamlit Community Cloud](https://share.streamlit.io/).
3. Crie um aplicativo apontando para o repositório e selecione `app.py`.
4. Publique e abra o endereço HTTPS gerado.
5. No celular, permita o acesso à câmera quando solicitado.

**Limitação de armazenamento:** o arquivo SQLite é criado no ambiente de execução. No Streamlit Community Cloud, arquivos locais não devem ser tratados como armazenamento durável. Reinícios, republicações ou mudanças de ambiente podem fazer com que os dados sejam perdidos. Use apenas dados fictícios nesta demonstração.

## Limitações conhecidas e segurança

- Não utilizar dados pessoais, inventário confidencial ou informações reais de uma instituição.
- Não há login corporativo, gestão de papéis, trilha de auditoria completa ou rotina de backup.
- A leitura de uma etiqueta comprova apenas que um código foi decodificado; não comprova por si só a autenticidade, a condição ou a presença permanente do patrimônio.
- O QR Code desta versão contém o código patrimonial em texto. Uma implantação real deve avaliar códigos opacos/aleatórios, validação de integridade e controles contra adulteração.
- O scanner carrega a biblioteca ZXing por um endereço CDN externo; uma implantação institucional deve fixar versões e avaliar a política de dependências e rede.
- O banco SQLite e os dados de exemplo são voltados à demonstração, não à operação multiusuário.

## Visão da Versão 2 — implantação real

A Versão 2 será planejada como uma aplicação web independente, **sem Streamlit**, executada em um servidor local no ambiente de trabalho. O desenho poderá incluir:

- Servidor web local e interface responsiva para celular.
- Banco de dados persistente na máquina/servidor local, com rotinas de backup e restauração.
- Alternativamente, banco e infraestrutura em nuvem — por exemplo, Supabase, se essa for a escolha do cliente.
- Autenticação, perfis de acesso e trilha de auditoria.
- Registro mais completo de vistoria, movimentações, fotos e justificativas.
- Relatórios PDF configuráveis e exportação dos resultados.
- Regras de validação, tratamento de duplicidades e revisão humana de divergências.
- Avaliação de reconhecimento de objetos em fotografias, caso seja necessário.

A arquitetura definitiva depende do ambiente, da política de TI, da quantidade de usuários, dos requisitos de segurança e das regras de retenção de dados. A implantação real requer análise e configuração específicas.

## Contato para implementação

Este repositório apresenta a ideia e a arquitetura inicial do projeto. Para avaliar uma implementação plena, adaptar o sistema a um ambiente de trabalho ou discutir requisitos específicos, entre em contato:

- **Responsável:** Luan Carlos Pinheiro Reis
- **E-mail:** `luandigitalversion@gmail.com`

## Status

**Versão 1 — protótipo demonstrativo em desenvolvimento.**  
A publicação deste código não representa certificação de segurança, garantia de disponibilidade nem adequação automática a ambientes institucionais.
