import sys
import StringIO

from doit import reporter
from doit.task import Task
from doit.exceptions import CatchedException
from doit.dependency import json #FIXME move json import to __init__.py


class TestConsoleReporter(object):

    def test_startTask(self):
        rep = reporter.ConsoleReporter(StringIO.StringIO(), True, True)
        rep.start_task(Task("t_name", None))
        # no output on start task
        assert "" in rep.outstream.getvalue()

    def test_executeTask(self):
        rep = reporter.ConsoleReporter(StringIO.StringIO(), True, True)
        def do_nothing():pass
        t1 = Task("with_action",[(do_nothing,)])
        rep.execute_task(t1)
        assert ".  with_action\n" == rep.outstream.getvalue()

    def test_executeGroupTask(self):
        rep = reporter.ConsoleReporter(StringIO.StringIO(), True, True)
        rep.execute_task(Task("t_name", None))
        assert "" == rep.outstream.getvalue()

    def test_skipUptodate(self):
        rep = reporter.ConsoleReporter(StringIO.StringIO(), True, True)
        rep.skip_uptodate(Task("t_name", None))
        assert "-- " in rep.outstream.getvalue()
        assert "t_name" in rep.outstream.getvalue()

    def test_skipIgnore(self):
        rep = reporter.ConsoleReporter(StringIO.StringIO(), True, True)
        rep.skip_ignore(Task("t_name", None))
        assert "!! " in rep.outstream.getvalue()
        assert "t_name" in rep.outstream.getvalue()


    def test_cleanupError(self, capsys):
        rep = reporter.ConsoleReporter(StringIO.StringIO(), True, True)
        exception = CatchedException("I got you")
        rep.cleanup_error(exception)
        err = capsys.readouterr()[1]
        assert "I got you" in err

    def test_teardownTask(self):
        rep = reporter.ConsoleReporter(StringIO.StringIO(), True, True)
        rep.teardown_task(Task("t_name", None))
        # no output on teardown task
        assert "" in rep.outstream.getvalue()

    def test_addSuccess(self):
        rep = reporter.ConsoleReporter(StringIO.StringIO(), True, True)
        rep.add_success(Task("t_name", None))
        # no output on success task
        assert "" in rep.outstream.getvalue()

    def test_runtimeError(self):
        msg = "runtime error"
        rep = reporter.ConsoleReporter(StringIO.StringIO(), True, True)
        assert None == rep.aborted
        # no imediate output
        rep.runtime_error(msg)
        assert msg == rep.aborted
        assert "" in rep.outstream.getvalue()
        # runtime errors abort execution
        rep.complete_run()
        got = rep.outstream.getvalue()
        assert msg in got
        assert "abort" in got

    def test_addFailure(self):
        rep = reporter.ConsoleReporter(StringIO.StringIO(), True, True)
        try:
            raise Exception("original exception message here")
        except Exception,e:
            catched = CatchedException("catched exception there", e)
        rep.add_failure(Task("t_name", None), catched)
        rep.complete_run()
        got = rep.outstream.getvalue()
        # description
        assert "Exception: original exception message here" in got, got
        # traceback
        assert """raise Exception("original exception message here")""" in got
        # catched message
        assert "catched exception there" in got


class TestExecutedOnlyReporter(object):
    def test_skipUptodate(self):
        rep = reporter.ExecutedOnlyReporter(StringIO.StringIO(), True, True)
        rep.skip_uptodate(Task("t_name", None))
        assert "" == rep.outstream.getvalue()

    def test_skipIgnore(self):
        rep = reporter.ExecutedOnlyReporter(StringIO.StringIO(), True, True)
        rep.skip_ignore(Task("t_name", None))
        assert "" == rep.outstream.getvalue()



class TestTaskResult(object):
    def test(self):
        def sample():
            print "this is printed"
        t1 = Task("t1", [(sample,)])
        result = reporter.TaskResult(t1)
        result.start()
        t1.execute()
        result.set_result('success')
        got = result.to_dict()
        assert t1.name == got['name'], got
        assert 'success' == got['result'], got
        assert "this is printed\n" == got['out'], got
        assert "" == got['err'], got
        assert got['started']
        assert 'elapsed' in got


class TestJsonReporter(object):

    def test_normal(self):
        output = StringIO.StringIO()
        rep = reporter.JsonReporter(output)
        t1 = Task("t1", None)
        t2 = Task("t2", None)
        t3 = Task("t3", None)
        t4 = Task("t4", None)
        expected = {'t1':'fail', 't2':'up-to-date',
                    't3':'success', 't4':'ignore'}
        # t1 fail
        rep.start_task(t1)
        rep.execute_task(t1)
        rep.add_failure(t1, Exception('hi'))
        # t2 skipped
        rep.start_task(t2)
        rep.skip_uptodate(t2)
        # t3 success
        rep.start_task(t3)
        rep.execute_task(t3)
        rep.add_success(t3)
        # t4 ignore
        rep.start_task(t4)
        rep.skip_ignore(t4)

        # just ignore these
        rep.cleanup_error(Exception('xx'))
        rep.teardown_task(t4)

        rep.complete_run()
        got = json.loads(output.getvalue())
        for task_result in got['tasks']:
            assert expected[task_result['name']] == task_result['result'], got

    def test_runtime_error(self):
        output = StringIO.StringIO()
        rep = reporter.JsonReporter(output)
        t1 = Task("t1", None)
        msg = "runtime error"
        assert None == rep.aborted
        rep.start_task(t1)
        rep.execute_task(t1)
        rep.add_success(t1)
        rep.runtime_error(msg)
        assert msg == rep.aborted
        assert "" in rep.outstream.getvalue()
        # runtime errors abort execution
        rep.complete_run()
        got = json.loads(output.getvalue())
        assert msg in got['err']


    def test_ignore_stdout(self):
        output = StringIO.StringIO()
        rep = reporter.JsonReporter(output)
        sys.stdout.write("info that doesnt belong to any task...")
        sys.stderr.write('something on err')
        t1 = Task("t1", None)
        expected = {'t1':'success'}
        rep.start_task(t1)
        rep.execute_task(t1)
        rep.add_success(t1)
        rep.complete_run()
        got = json.loads(output.getvalue())
        assert expected[got['tasks'][0]['name']] == got['tasks'][0]['result']
        assert "info that doesnt belong to any task..." == got['out']
        assert "something on err" == got['err']
