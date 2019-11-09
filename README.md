## See project wiki

**Supported Public Clouds**
  * Google Cloud
  * Amazon AWS
  * Azure (started)

**Support for VMWare**
  * ESXi

**Kubernetes Variants supported**
  * Docker
  * Docker (bootstrapping), Cri-O as container runtime
  * Pod Networks: Flannel,	Calico, Calico (Policy) & Flannel (Networking)
  * Rook-Ceph Block Storage on worker nodes
  * Helm

**Software Components**
  * PostgreSQL 10.10
  * Deep Security 12.5 FR
  * Deep Security Smart Check Latest
  * Kubernetes 1.14.4
  * Cri-O 1.14
  * Docker 18.09.8
  * Helm 2.14.2
  * Rook-Ceph 1.0.4
  * Go 1.12.7
  * Jenkins (by helm) 2.190.1
  * GitLab (by helm) Latest
  * GitLab (by docker) Latest
  * Linkerd Latest
  * Docker Registry 2.7.1

**Preconfigured internet accessible ports for the installed services**
  * 4119: Deep Security
  * 8443: GitLab (on docker)
  * 30000: Kubernetes Dashboard
  * 30001: Rook-Ceph Dashboard
  * 30002: Linkerd Dashboard
  * 30010: Deep Security Smart Check
  * 30011: Deep Security Smart Check Registry
  * 30012: Certificate Server (Serving Smart Checks Certificate)
  * 30013: Jenkins
  * 30014, 30015, 30016: GitLab (on k8s)
  * 30017: Docker Registry

**Note:** Jenkins does require docker as the container runtime. Cri-o is not supported

**Note:** The Jenkins chart does have a bug within it's role binding, resulting in permission denied for the pod-dind to request persistent storage

**Note:** GitLab (on k8s) is currently not functional

**Note:** GitLab requires a publicly resolvable domain name (e.g. no-ip.com) to enable trusted certificates. The defined name is moadsd-ng.hopto.org but may be changed within the vars files. The dns name must point to the correct ip of the GitLab service before the deployment.

**Note:**
When going the ESX variant, you need to prepare e.g. 4 ubuntu bionic servers beforehand. For a naming example review the hosts file provided within this repo. Lastly, you need to set the primary username / password within environment_esx_secrets.yml.

**Initial configuration of Deep Security:**
  * enable agent based activation
  * download required agents to local software store

**Demo setting up MOADSD-NG on GCP**
<a href="https://asciinema.org/a/qCccOnLbFCWcYYIVaGU74alkr?speed=6&autoplay=1" target="_blank"><img src="https://asciinema.org/a/qCccOnLbFCWcYYIVaGU74alkr.svg" /></a>
