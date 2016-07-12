"""
    Copyright (c) 2016 Hubert Jarosz. All rights reserved.
    Licensed under the MIT license. See LICENSE file in the project root for full license information.
"""

import configparser
import time
import os
import subprocess
import sys
import datetime
import traceback
import shutil
import tempfile
import pathlib


class Deployer:
    @staticmethod
    def __log_error(error):
        print(datetime.datetime.now(), "ERROR:", str(error), file=sys.stderr)

    def __init__(self, config_file):
        self.running = True
        config = configparser.ConfigParser()
        config.read(str(config_file))

        if "main" not in config.sections():
            raise Exception("no [main] section in config.ini")

        try:
            self.sleep = config.getfloat("main", "sleep_seconds", fallback=0.0)
        except:
            raise Exception("Invalid sleep time!")
        self.type = config.get("main", "repository_type", fallback="")
        self.url = config.get("main", "repository_url", fallback="")
        data = config.get("main", "data_dir", fallback="")
        self.name = config.get("main", "name", fallback="")
        self.scp_url = config.get("main", "scp_url", fallback="")
        self.script = config.get("extra", "script", fallback="")
        self.scp_settings = config.get("extra", "scp_settings", fallback="")

        if "" in (self.type, self.url, data, self.name, self.scp_url):
            raise Exception("Some keys are missing from conf!")

        if self.type != "git":
            raise Exception("Only git is supported!")

        if self.sleep <= 0.0:
            raise Exception("Sleep time must be higher than 0.0!")

        if self.script != "" and not os.path.isfile(self.script):
            raise Exception("Script does not exist!")

        self.data_dir = pathlib.Path(data)

        if not self.data_dir.is_dir():
            raise Exception("Data directory does not exist!")

        self.repo_dir = self.data_dir / "repo"
        self.package_dir = self.data_dir / "to_send"

    def run(self):
        clone = True
        if self.repo_dir.is_dir():
            clone = False
            try:
                remotes = subprocess.check_output(
                    ["git", "remote", "-v"],
                    cwd=str(self.repo_dir),
                    stderr=subprocess.STDOUT)
                if not remotes.decode("UTF-8").find(self.url):
                    shutil.rmtree(str(self.repo_dir))
                    clone = True
            except:
                shutil.rmtree(str(self.repo_dir))
                clone = True
        if clone:
            try:
                subprocess.check_output(
                    ["git", "clone", "--mirror", self.url, str(self.repo_dir)],
                    stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                raise Exception(e.output)
            except:
                raise Exception("Fatal error during cloning.")

        while self.running:
            try:
                self.__tick()
            except:
                self.__log_error("Tick failed.")
                traceback.print_exception(*sys.exc_info())
            time.sleep(self.sleep)
            time.sleep(0.1)

    def __tick(self):
        try:
            subprocess.check_output(
                ["git", "remote", "update"],
                cwd=str(self.repo_dir),
                stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            self.__log_error(e.output)
            return

        for tag in self.__get_new_tags():
            try:
                self.__process_tag(tag)
            except:
                self.__log_error("Error while processing tag " + tag)
                raise

        self.__send_packages()

    def __get_new_tags(self):
        try:
            tags = subprocess.check_output(
                ["git", "tag", "--sort", "version:refname"],
                cwd=str(self.repo_dir),
                stderr=subprocess.STDOUT).decode("UTF-8")
        except subprocess.CalledProcessError as e:
            self.__log_error(e.output)
            return []

        try:
            last_tag_file = (self.data_dir / "last_tag").open("r+")
        except FileNotFoundError:
            last_tag_file = (self.data_dir / "last_tag").open("w+")
        last_tag = last_tag_file.read().strip()

        try:
            tmp = tags.split(last_tag)
            if len(tags) > 1:
                new_tags = tmp[1].strip()
            else:
                new_tags = tmp[0].strip()
        except ValueError:
            new_tags = tags.strip()

        new_tags_list = []

        if len(new_tags) > 0:
            new_tags_list = new_tags.split("\n")
        if new_tags_list:
            last_tag_file.write(new_tags_list[-1] + "\n")
            last_tag_file.close()

        return new_tags_list

    def __process_tag(self, tag):
        tag_dir = tempfile.mkdtemp()
        try:
            try:
                subprocess.check_output(
                    ["git", "clone", str(self.repo_dir), "."],
                    cwd=tag_dir,
                    stderr=subprocess.STDOUT)
                subprocess.check_output(
                    ["git", "checkout", "tags/"+tag],
                    cwd=tag_dir,
                    stderr=subprocess.STDOUT)
                shutil.rmtree(tag_dir+"/.git")
                try:
                    os.remove(tag_dir+"/.gitignore")
                except OSError:
                    pass
                if self.script != "":
                    subprocess.check_output(
                        [self.script, tag, tag_dir],
                        cwd=tag_dir,
                        stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                self.__log_error(e.output)
                raise

            try:
                os.chdir(str(self.package_dir))
            except OSError:
                self.package_dir.mkdir()
                os.chdir(str(self.package_dir))

            shutil.make_archive(self.name+"-"+tag, "zip", tag_dir, ".")
        except:
            shutil.rmtree(tag_dir)
            raise

    def __send_packages(self):
        for f in self.package_dir.iterdir():
            if f.is_file():
                try:
                    subprocess.check_output(
                        ["scp", self.scp_settings, str(f.resolve()), self.scp_url],
                        cwd=str(self.package_dir),
                        stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as e:
                    self.__log_error(e.output)
                    continue
            os.remove(str(f.resolve()))
