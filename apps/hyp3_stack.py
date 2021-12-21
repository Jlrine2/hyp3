import dataclasses
import json
from typing import List, Optional

from aws_cdk import (
    Stack,
    CfnParameter,
    cloudformation_include,
)
from constructs import Construct


@dataclasses.dataclass
class HyP3Config:
    domain: str
    edl_username: str
    edl_password: str
    certificate_arn: str
    image_tag: str
    product_lifetime: int
    vpc_id: str
    subnet_ids: List[str]
    monthly_quota_per_user: int
    banned_cidr_blocks: List[str]
    default_max_vcpus: int
    extended_max_vcpus: int
    monthly_compute_budget: int
    required_surplus: int
    permissions_boundary_arn: Optional[str]
    earthdata_cloud: bool
    ami_id: str
    auth_key: str = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDBU3T16Db/88XQ2MTHgm9uFALjSJAMSejmVL+tO0ILzHw2OosKlVb38urmIGQ+xMPXTs1AQQYpJ/CdO7TaJ51pv4iz+zF0DYeUhPczsBEQYisLMZUwedPm9QLoKu8dkt4EzMiatQimBmzDvxxRkAIDehYh468phR6zPqIDizbgAjD4qgTd+oSA9mDPBZ/oG1sVc7TcoP93FbO9u1frzhjf0LS1H7YReVP4XsUTpCN0FsxDAMfLpOYZylChkFQeay7n9CIK8em4W4JL/T0PC218jXpF7W2p92rfAQztiWlFJc66tt45SXAVtD1rMEdWGlzze4acjMn4P7mugHHb17igtlF82H/wpdm84qTPShvBp/F4YZejgAzOAxzKVbCQ8lrApk1XYVDRAVk3AphfvNK5IC/X9zDSXstH9U94z8BTjkL2fR4eKzFu5kkvVoGHAACIv72QvH06Vwd0PNzLyaNXr9D5jO61EbR4RfpbzvAG0IzgXsUq0Rj7qwvzTCu6yLwTi/fn9bmRaOQNPtBch4ai5w7cfUWe2r7ZPv31AXPm1A+aGXvYTEZkiQMrBN/dXlNdUmafNNDoMBm/frQhMl+2DZp+C9GXCr2Z/JmYUHO8PaEj6UyYTkkrmtZNlZ43Nd2TblPEzL0pprJM9MxEf2Peaai8GKmTJz6C5tSGU+XdZQ== root@9dce6b43747e'
    auth_algorithm: str = 'RS256'

class HyP3Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        parameters = CfnParameter(self, 'ParametersArn', type='String',
                                  description='Location of a parameter in SSM with json config payload')
        domain = CfnParameter(self, 'Domain', type='String', description='domain name for API')
        config = HyP3Config(domain=domain.value_as_string, **json.loads(parameters.value_as_string))

        stack = cloudformation_include.CfnInclude(self, "rootstack",
                                                  template_file='main-cf.yml',
                                                  parameters=dict(
                                                      VpcId=config.vpc_id,
                                                      subnetIds=','.join(config.subnet_ids),
                                                      EDLUsername=config.edl_username,
                                                      EDLPassword=config.edl_password,
                                                      ImageTag=config.image_tag,
                                                      ProductLifetimeInDays=config.product_lifetime,
                                                      AuthPublicKey=config.auth_key,
                                                      AuthAlgorithm=config.auth_algorithm,
                                                      DomainName=config.domain,
                                                      CertificateArn=config.certificate_arn,
                                                      MonthlyJobQuotaPerUser=config.monthly_quota_per_user,
                                                      BannedCidrBlocks=config.banned_cidr_blocks,
                                                      PermissionsBoundaryPolicyArn=config.permissions_boundary_arn,
                                                      EarthdataCloud=config.earthdata_cloud,
                                                      AmiId=config.ami_id,
                                                      DefaultMaxvCpus=config.default_max_vcpus,
                                                      ExpandedMaxvCpus=config.extended_max_vcpus,
                                                      MonthlyComputeBudget=config.monthly_compute_budget,
                                                      RequiredSurplus=config.required_surplus,
                                                      SystemAvailable=True,
                                                  ))
