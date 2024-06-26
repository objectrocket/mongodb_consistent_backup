import os
import logging


from mongodb_consistent_backup.Common import LocalCommand
from mongodb_consistent_backup.Pipeline import PoolThread


class TarThread(PoolThread):
    def __init__(self, backup_dir, output_file, compression='none', verbose=False, binary="tar"):
        super(TarThread, self).__init__(self.__class__.__name__, compression)
        self.compression_method = compression
        self.backup_dir         = backup_dir
        self.output_file        = output_file
        self.verbose            = verbose
        self.binary             = binary

        self._command = None

    def close(self, exit_code=None, frame=None):
        if self._command and not self.stopped:
            logging.debug("Stopping running tar command: %s" % self._command.command)
            del exit_code
            del frame
            self._command.close()
            self.stopped = True

    def run(self):
        if os.path.isdir(self.backup_dir):
            if not os.path.isfile(self.output_file):
                try:
                    backup_base_dir  = os.path.dirname(self.backup_dir)
                    backup_base_name = os.path.basename(self.backup_dir)
                    output_file_dir = os.path.dirname(self.output_file)
                    output_file_basename= os.path.basename(self.output_file)
                    admin_backup_file = output_file_dir+"/" +"_".join(["admin",output_file_basename])
                    config_backup_file = output_file_dir+"/" +"_".join(["config",output_file_basename])

                    log_msg   = "Archiving directory: %s" % self.backup_dir
                    cmd_flags = ["--exclude", "admin", "--exclude", "config" ,"-C", backup_base_dir, "-c", "-f", self.output_file, "--remove-files"]
                    admin_command_flags = ["-C", self.backup_dir +"/dump/", "-c", "-f", admin_backup_file, "--remove-files", "--ignore-failed-read",]
                    config_command_flags = ["-C", self.backup_dir +"/dump/", "-c", "-f", config_backup_file, "--remove-files", "--ignore-failed-read",]
                    

                    if self.do_gzip():
                        log_msg = "Archiving and compressing directory: %s" % self.backup_dir
                        cmd_flags.append("-z")
                        admin_command_flags.append("-z")
                        config_command_flags.append("-z")

                    cmd_flags.append(backup_base_name)
                    admin_command_flags.append("admin")
                    config_command_flags.append("config")
                    logging.info(log_msg)
                    self.running  = True
                    self._command = LocalCommand(self.binary, cmd_flags, admin_command_flags, config_command_flags, self.verbose)
                    self.exit_code = self._command.run()
                except Exception, e:
                    return self.result(False, "Failed archiving file: %s!" % self.output_file, e)
                finally:
                    self.running   = False
                    self.stopped   = True
                    self.completed = True
            else:
                return self.result(False, "Output file: %s already exists!" % self.output_file, None)
            return self.result(True, "Archiving successful.", None)

    def result(self, success, message, error):
        return {
            "success":   success,
            "message":   message,
            "error":     error,
            "directory": self.backup_dir,
            "exit_code": self.exit_code
        }
