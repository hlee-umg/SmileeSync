"""Infraestructura de SmileeSync en AWS (CDK, Python).

Estrategia de bajo costo: UNA sola instancia EC2 t3.small que ejecuta
Django + Gunicorn + Nginx + PostgreSQL. Sin RDS, sin NAT Gateway ni Load
Balancer, para no consumir los créditos del Free Tier. El modelo de ML se
entrena fuera del servidor y solo se despliega el archivo entrenado.
"""
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
)
from constructs import Construct

# Parámetro público de Canonical con el AMI vigente de Ubuntu 24.04 (x86_64)
UBUNTU_2404_SSM = (
    "/aws/service/canonical/ubuntu/server/24.04/stable/"
    "current/amd64/hvm/ebs-gp3/ami-id"
)


class SmileeSyncStack(Stack):
    def __init__(self, scope: Construct, cid: str, **kwargs) -> None:
        super().__init__(scope, cid, **kwargs)

        # VPC por defecto (evita costos de NAT/subredes privadas)
        vpc = ec2.Vpc.from_lookup(self, "VpcDefault", is_default=True)

        # Grupo de seguridad: SSH, HTTP y HTTPS
        sg = ec2.SecurityGroup(self, "SmileeSG", vpc=vpc,
                               description="SmileeSync web + ssh",
                               allow_all_outbound=True)
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "SSH")
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "HTTP")
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "HTTPS")

        # Script de arranque: instala dependencias base del servidor
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "apt-get update -y",
            "apt-get install -y python3-venv python3-pip nginx postgresql "
            "postgresql-contrib git",
            "systemctl enable --now postgresql nginx",
        )

        instancia = ec2.Instance(
            self, "SmileeServer",
            instance_type=ec2.InstanceType("t3.small"),   # 2 vCPU / 2 GB
            machine_image=ec2.MachineImage.from_ssm_parameter(
                UBUNTU_2404_SSM, os=ec2.OperatingSystemType.LINUX),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=sg,
            user_data=user_data,
            key_name="smileesync-key",   # crear el key pair antes de desplegar
        )

        eip = ec2.CfnEIP(self, "SmileeEIP")
        ec2.CfnEIPAssociation(self, "SmileeEIPAssoc",
                              eip=eip.ref, instance_id=instancia.instance_id)

        CfnOutput(self, "IPPublica", value=eip.ref)
        CfnOutput(self, "IdInstancia", value=instancia.instance_id)
