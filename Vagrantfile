# vagrant plugin install vagrant-disksize
IMAGE_NAME = "ubuntu/bionic64"
N = 3

$script = <<-'SCRIPT'
sed -i 's/PasswordAuthentication no/#PasswordAuthentication no/g' /etc/ssh/sshd_config
systemctl restart sshd
encpass=$(openssl passwd -crypt PASSWORD)
useradd -m -s /bin/bash -p $encpass k8s
echo "k8s ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/custom-users
sudo apt-get install -y python python-simplejson
SCRIPT

Vagrant.configure("2") do |config|
    config.ssh.insert_key = false
    config.disksize.size = '50GB'
    config.vm.provider "virtualbox" do |v|
        v.memory = 8192
        v.cpus = 2
    end

    config.vm.define "k8smaster" do |master|
        master.vm.box = IMAGE_NAME
        master.vm.network "public_network"
        master.vm.hostname = "vk8smaster"
        master.vm.provision "shell", inline: $script
    end

    (1..N).each do |i|
        config.vm.define "k8sworker#{i}" do |worker|
            worker.vm.box = IMAGE_NAME
            worker.vm.network "public_network"
            worker.vm.hostname = "vk8sworker#{i}"
            worker.vm.provision "shell", inline: $script
        end
    end
end
