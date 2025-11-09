ALLOW_HTTP_FROM_ANYWHERE = {
    'IpProtocol': 'tcp',
    'FromPort': 80, # default port for HTTP
    'ToPort': 80,
    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
}
ALLOW_APP_PORT_8000_FROM_ANYWHERE = {
    'IpProtocol': 'tcp',
    'FromPort': 8000, # default port for the applications like flask
    'ToPort': 8000,
    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
}
ALLOW_SSH_FROM_ANYWHERE = {
    'IpProtocol': 'tcp',
    'FromPort': 22, # default port for SSH
    'ToPort': 22,
    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
}
