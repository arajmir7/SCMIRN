# Terraform Notes

This folder is reserved for Infrastructure as Code modules (VPC, registry, compute, DNS, secrets).

Recommended module layout:

```text
terraform/
|-- envs/
|   |-- dev/
|   `-- prod/
|-- modules/
|   |-- network/
|   |-- compute/
|   `-- observability/
`-- README.md
```

