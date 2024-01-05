# Events scheduler

## Description

This is a small project called *Events scheduler*. It consists of a 
web application built using Django Framework and Postgres as DBMS. The main focus 
was to create a simple application which can handle fast millions of entries in database.

It consists of following features:
 - Users can browse the website and look for events they are interested in
 - Users can list new events using an account
 - Users can update the account information
 - Users can register using email address (which is verified)
 - They can join / withdraw from events
 - Registered users can also update / delete created events

## Setting up

### Requirements

A UNIX like system is required for a smoother setup. (MacOS or Ubuntu >=20.4)

A version of >=python3.10 is required. 

The project is isolated using Docker. The version used is: 
- Docker 24.0.2

Any version of Docker >= 20.10 should work also.


Root of the project is: **events-scheduler**. All of the following scripts are executed relative to events-scheduler/.

First step is to create a virtual environment by running:

```shell
python3.10 -m venv venv
```

Once the virtual environment has been created, activate the interpreter. Assuming that you are in the root
of the project: 
```shell
source venv/bin/activate
```

Now we are ready to build the project. For this, execute:

```shell
bash build.sh
```

### Initial data

I have created a dummy dataset which consists of million of entries.
If you have git-lfs installed, then skip this part. Otherwise, before pulling the data, install git lfs since the dump has more than 100 MB.

For macOS:
```shell
brew install git-lfs
```
should do the job. For other OS, please visit: [this github repo for instalation](https://github.com/git-lfs/git-lfs?utm_source=gitlfs_site&utm_medium=installation_link&utm_campaign=gitlfs#installing). 

In the root of the project, a file named **initial_data.json** will be found. It contains dumy initial  data.
It has tens of thousands of events and a couple of thousands users and millions of users registered to events.
If you would like to load data, please run after build is successfully done:


```shell
bash scripts/db/load_dump.sh
```

The process of loading data might take a while since it is using Django's way of loading data.


## Testing

To run an individual test, execute **run_test.sh**. It has one required positional argument which
should be the path to the test:

```shell
bash scripts/tests/run_test.sh <path/to/the/test>
```

For a better test tracking record, I used *coverage* library. 

To run all tests of the application, execute **run_coverage.sh**. 
```shell
bash scripts/tests/run_coverage.sh
```

To generate the html file based on last coverage run, please execute:
```shell
bash scripts/tests/run_html.sh
```

## Other setup

I have implemented a password reset and verification of the email flow. In my configuration I have used gmail with 2-step authorization enabled and 
I have created a dummy password for sending emails. I added it in .env file. 
Please update the .env file accordingly.

Cheers !
