# auto-arch-analyzer

### Variáveis de Ambiente para Execução Local

Para rodar o Terraform localmente, você precisa exportar as seguintes variáveis de ambiente com suas credenciais AWS:

```sh
export AWS_ACCESS_KEY_ID="<your-access-key-id>"
export AWS_SECRET_ACCESS_KEY="<your-secret-access-key>"
export AWS_SESSION_TOKEN="<your-session-token>"
export AWS_DEFAULT_REGION="us-east-1"
```

Depois de exportar essas variáveis, você pode executar os comandos Terraform normalmente:


### Installation

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Initialize Terraform:
    ```sh
    terraform init
    ```

3. Validate the Terraform configuration:
    ```sh
    terraform validate
    ```

4. Format the Terraform configuration:
    ```sh
    terraform fmt


### Configurar Variáveis de Ambiente no GitHub

Acesse o repositório no GitHub → Settings → Secrets and variables → Actions → Repository secrets

Adicione as seguintes variáveis:

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `AWS_ACCESS_KEY_ID` | [Access Key criada na Etapa 3] | Chave de acesso do usuário IAM |
| `AWS_SECRET_ACCESS_KEY` | [Secret Key criada na Etapa 3] | Chave secreta do usuário IAM |
| `AWS_ACCOUNT_ID` | [ID da conta AWS] | ID numérico da conta AWS (12 dígitos) |
| `AWS_REGION` | `us-east-1` | Região AWS onde será feito o deploy |
| `TERRAFORM_STATE_BUCKET` | [Nome do bucket criado na Etapa 4] | Bucket S3 para armazenar o estado do Terraform |


### Terraform State Backend Configuration

O estado do Terraform é armazenado em um bucket S3 com a seguinte configuração:

- **Bucket S3**: `auto-arch-analyzer-backend-terraform-state-files-dev`
- **State File Path**: `back_end_state_file/terraform.tfstate`

Esta configuração é utilizada durante a execução de `terraform init` e é automaticamente aplicada pelo workflow de CI/CD.
