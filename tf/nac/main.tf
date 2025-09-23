terraform {
  required_providers {
    aci = {
      source = "CiscoDevNet/aci"
    }
  }
}

variable "apic_username" {
  type=string
}

variable "apic_password" {
  type=string
}

variable "apic_url" {
  type=string
}

provider "aci" {
  username = "${var.apic_username}"
  password = "${var.apic_password}"
  url      = "${var.apic_url}"
  insecure = true
}

module "aci" {
  source  = "netascode/nac-aci/aci"
  version = "1.1.0"

  yaml_directories = ["data"]

  manage_access_policies    = true
  manage_fabric_policies    = true
  manage_pod_policies       = true
  manage_node_policies      = true
  manage_interface_policies = true
  manage_tenants            = true
}
