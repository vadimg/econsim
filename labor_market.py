import random

random.seed(42) # make it deterministic

class Job(object):
    _jid_counter = 0

    def __init__(self, employer, productivity, salary):
        self.jid = self._jid_counter
        self.employer = employer
        self.productivity = productivity
        self.salary = salary
        self.applications = []

        Job._jid_counter += 1

    def apply_for(self, worker):
        self.applications.append(worker)

    def take_job(self, worker):
        #print 'job', self.jid, 'taken for', self.salary, 'by worker with', worker.productivity
        worker.job = self
        self.employer.add_worker(worker, self)

    def quit_job(self, worker):
        worker.job = None
        self.employer.remove_worker(worker, self)


class LaborMarket(object):
    def __init__(self):
        self.jobs = []

    def add_job(self, job):
        self.jobs.append(job)

    def remove_job(self, job):
        self.jobs.remove(job)

    def find_jobs(self, productivity, salary):
        return [x for x in self.jobs if x.productivity <= productivity and x.salary >= salary]


labor_market = LaborMarket()

class Worker(object):
    def __init__(self):
        self.productivity = random.paretovariate(1)
        self._salary_ask = self.productivity * 10
        self.job = None
        self.offered_jobs = []

    @property
    def salary_ask(self):
        if self.job is None:
            return self._salary_ask
        else:
            return self.job.salary * 1.1

    def tick(self):
        # get a job
        if self.offered_jobs:
            # pick job with highest salary
            self.offered_jobs.sort(key=lambda x: x.salary)
            job = self.offered_jobs[-1]

            if self.job is None:
                job.take_job(self)
            elif job.salary >= self.salary_ask:
                # switch jobs
                self.job.quit_job(self)
                job.take_job(self)

            # reset job offers
            self.offered_jobs = []

        # search for jobs
        jobs = labor_market.find_jobs(self.productivity, self.salary_ask)

        if not jobs:
            if self.job is None:
                # can't find a job, lower our standards
                self._salary_ask *= .9
        else:
            for job in jobs:
                job.apply_for(self)

    def offer_job(self, job):
        self.offered_jobs.append(job)


class Employer(object):
    def __init__(self):
        self.employees = []
        self.open_jobs = []

        self._add_job(self._create_job())

    def _create_job(self):
        productivity = random.paretovariate(1)
        return Job(employer=self,
                   productivity=productivity,
                   salary=productivity * .1)

    def _add_job(self, job):
        self.open_jobs.append(job)
        labor_market.add_job(job)

    def add_worker(self, worker, job):
        job.applications = []
        self.remove_job(job)
        self.employees.append(worker)

    def remove_worker(self, worker, job):
        self.employees.remove(worker)
        self._add_job(job)

    def remove_job(self, job):
        self.open_jobs.remove(job)
        labor_market.remove_job(job)

    @property
    def surplus(self):
        return sum(x.productivity - x.job.salary for x in self.employees)

    @property
    def hiring_commitment(self):
        return sum(x.salary for x in self.open_jobs)

    def tick(self):
        # based on surplus, create jobs
        surplus = self.surplus - self.hiring_commitment

        job = self._create_job()
        if job.salary <= surplus:
            self._add_job(job)

        for job in self.open_jobs:
            if job.applications:
                # offer the cheapest worker the job
                # TODO: this assumes that everyone who applied is qualified
                # (which is true in this sim, but you should verify it as an employer IRL)
                job.applications.sort(key=lambda x: x.salary_ask)
                job.applications[0].offer_job(job)
            else:
                # no job applications, see if we can raise salary
                if job.salary < job.productivity:
                    job.salary = min(job.salary * 1.1, job.productivity)
                else:
                    # can't raise salary, so remove job
                    self.remove_job(job)

            # reset applications
            job.applications = []



class World(object):
    def __init__(self):
        self.workers = [Worker() for _ in xrange(100)]
        self.employers = [Employer() for _ in xrange(10)]
        self.objects = self.workers + self.employers

    def tick(self):
        for o in self.objects:
            o.tick()

    @property
    def employed_workers(self):
        return [x for x in self.workers if x.job]

    @property
    def employment(self):
        return float(len(self.employed_workers)) / len(self.workers)

    @property
    def max_unfilled_salary(self):
        salaries = [y.salary for x in self.employers for y in x.open_jobs]

        return max(salaries)

    @property
    def avg_salary(self):
        # unemployed count as 0 salary
        salaries = [x.job.salary for x in self.employed_workers]

        return float(sum(salaries)) / len(self.workers)

    @property
    def unfilled_jobs(self):
        unfilled = sum(len(x.open_jobs) for x in self.employers)
        assert(unfilled == len(labor_market.jobs))
        return unfilled

    @property
    def employer_surplus(self):
        return sum(x.productivity - x.job.salary for x in self.employed_workers)


world = World()

for x in xrange(10000):
    print x,
    world.tick()
    print world.employment, world.avg_salary, world.unfilled_jobs, world.employer_surplus, world.max_unfilled_salary
