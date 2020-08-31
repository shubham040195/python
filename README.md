# test
Program accepts directory path as a input, it manages map of key-value where key is the hashmap of file and value is the path of file.

Command to build docker image:

docker build . -f <dockerfile-name> -t <imagename>

Command to run docker container:

docker run -d -v <filepath>:/home <imagename>

You can pass directroy path as an argument to container . By default it will take home directory.

After running the container we can check logs of container using below command to check the output-

docker logs <containerid>
