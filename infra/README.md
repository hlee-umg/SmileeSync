# Infraestructura (AWS CDK)

Despliega SmileeSync en una sola instancia EC2 `t3.small` de bajo costo.

## Requisitos
- AWS CLI configurado (`aws configure`).
- Node.js + `npm i -g aws-cdk`.
- Un key pair EC2 llamado `smileesync-key`.

## Uso
```bash
cd infra
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cdk bootstrap      # solo la primera vez
cdk synth
cdk deploy
```

> Nota: verificar el AMI de Ubuntu 24.04 vigente en la región antes de desplegar.
