# IMAGE_NAME = "bento/ubuntu-18.04"
# IMAGE_NAME = "ubuntu/bionic64"
IMAGE_NAME = "generic/ubuntu1804"
N = 3

$script = <<-'SCRIPT'
encpass=$(openssl passwd -crypt p455w0rd)
useradd -m -s /bin/bash -p $encpass trendmicro
echo "trendmicro ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/custom-users
sudo apt-get install -y python python-simplejson
SCRIPT

Vagrant.configure("2") do |config|
    config.ssh.insert_key = false

    config.vm.provider "virtualbox" do |v|
        v.memory = 8192
        v.cpus = 2
    end

    config.vm.define "k8smaster" do |master|
        master.vm.box = IMAGE_NAME
        master.vm.network "public_network"
        master.vm.hostname = "k8smaster"
        master.vm.provision "shell", inline: $script
    end

    (1..N).each do |i|
        config.vm.define "k8sworker#{i}" do |worker|
            worker.vm.box = IMAGE_NAME
            worker.vm.network "public_network"
            worker.vm.hostname = "k8sworker#{i}"
            worker.vm.provision "shell", inline: $script
        end
    end
end
