import jenkins
import jenkins

server = jenkins.Jenkins('http://localhost:8080', username='admin', password='e90f9f392aad4b4fa1f75bb62c90768c', timeout=5)
print(server.jobs_count())

server.create_job('empty', jenkins.EMPTY_CONFIG_XML)
jobs = server.get_jobs()
print(jobs)