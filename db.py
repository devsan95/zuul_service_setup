def create_db(ip, user, passw, port):
    import subprocess
    args_linux_host_ip = ip
    args_database_user = user
    args_database_password = passw
    args_database_port = port
    subprocess.run(["powershell", "-Command", f"C:\\'Program Files'\\HeidiSQL\\heidisql.exe --nettype=0 --host={args_linux_host_ip} --library=libmariadb.dll -u={args_database_user} -p={args_database_password} --port={args_database_port} -db='test_zuul;test_jayant;test_maria'"])
