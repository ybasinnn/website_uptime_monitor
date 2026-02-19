terraform {
  cloud {
    organization = "YordanOrg"
    workspaces {
      name = "website_check_serverless"
    }
  }


  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.17.0"
    }
  }


  required_version = ">= 1.13"
}


provider "aws" {
  region = var.aws_region
}