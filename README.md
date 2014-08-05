AwsInfra
========

This project aims to create scripting tools in order to easily manage Amazon AWS infrastructure.

Usage: python awsinfra --{start|stop|status}=[I[List of Instance IDs]],[V]

Examples:
  1. python awsinfra --status=I,V                                            ->  List all instances and vpns
  2. awsinfra --status=V                                                     ->  List all vpns
  3. awsinfra --status=I{r-ec999de4,r-ec999de5},V                            ->  List only instances IDs and vpns

Vpn in this version is hardcoded (e.g. Customer Private Gateway, Virtual Private Gateway, CIDR, etc.)
Vpn doesn't allow list of IDs

