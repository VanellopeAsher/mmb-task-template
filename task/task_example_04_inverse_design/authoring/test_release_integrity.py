"""Release integrity regression. Networking is mocked, never tested live here."""
from pathlib import Path
import json
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from release_hash import content_sha256

HERE=Path(__file__).resolve().parent
TASK=HERE.parent
PACKAGE=TASK.parents[1]
RELEASE=PACKAGE/'agent_release'/TASK.name
MANIFEST=HERE/'release_manifest.json'

class ReleaseIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.release=self.root/'release'
        shutil.copytree(RELEASE,self.release)

    def check_release(self,expected,manifest=MANIFEST):
        command=[sys.executable,str(HERE/'check_release.py'),'--release-root',str(self.release),'--manifest',str(manifest)]
        result=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def normalize_all(self,ending):
        for path in self.release.rglob('*'):
            if path.is_file():
                content=path.read_bytes().replace(b'\r\n',b'\n')
                path.write_bytes(content if ending=='LF' else content.replace(b'\n',b'\r\n'))

    def test_original(self):
        self.assertTrue(self.check_release(0)['passed'])

    def test_linux_lf(self):
        self.normalize_all('LF')
        self.assertTrue(self.check_release(0)['passed'])

    def test_windows_crlf(self):
        self.normalize_all('CRLF')
        self.assertTrue(self.check_release(0)['passed'])

    def test_mixed_endings(self):
        path=self.release/'problem.md'
        content=path.read_bytes().replace(b'\r\n',b'\n')
        path.write_bytes(content.replace(b'\n',b'\r\n',2))
        self.assertTrue(self.check_release(0)['passed'])

    def test_substantive_text_edit(self):
        path=self.release/'problem.md'
        path.write_bytes(path.read_bytes()+b'\nINJECTED ANSWER')
        self.assertIn('problem.md',self.check_release(1)['altered'])

    def test_numeric_data_edit(self):
        data=next(p for p in (self.release/'environment/data').glob('*.json') if p.name!='answer_contract.json')
        raw=data.read_bytes()
        position=next(i for i,b in enumerate(raw) if 48<=b<=57)
        data.write_bytes(raw[:position]+str((raw[position]-48+1)%10).encode()+raw[position+1:])
        self.assertIn(data.relative_to(self.release).as_posix(),self.check_release(1)['altered'])

    def test_extra_answer_file(self):
        (self.release/'answer.json').write_bytes(b'{}')
        self.assertIn('answer.json',self.check_release(1)['unexpected'])

    def test_missing_file(self):
        (self.release/'problem.md').unlink()
        self.assertIn('problem.md',self.check_release(1)['missing'])

    def test_invalid_utf8(self):
        (self.release/'problem.md').write_bytes(b'\xff')
        self.assertIn('problem.md',self.check_release(1)['invalid_encoding'])

    def test_legacy_manifest_rejected(self):
        legacy=json.loads(MANIFEST.read_text(encoding='utf-8'))
        legacy.pop('hash_policy')
        candidate=self.root/'old_manifest.json'
        candidate.write_text(json.dumps(legacy),encoding='utf-8')
        self.check_release(1,manifest=candidate)

    def test_normalization_does_not_ignore_other_edits(self):
        path=self.root/'sample.txt'
        path.write_bytes(b'1\r\n2\r\n')
        original=content_sha256(path)
        path.write_bytes(b'1\n2\n')
        self.assertEqual(content_sha256(path),original)
        for content in (b'1 \n2\n',b'1\n3\n',b'1\n2',b'1\r2\r',b'\xef\xbb\xbf1\n2\n'):
            path.write_bytes(content)
            self.assertNotEqual(content_sha256(path),original)

    def test_runtime_probe_uses_same_policy(self):
        workspace=self.root/'workspace'
        workspace.mkdir()
        for folder in ('data','tools','skills'):
            shutil.copytree(self.release/'environment'/folder,workspace/folder)
        for name in ('ACCESS_POLICY.md','requirements.txt'):
            shutil.copyfile(self.release/'environment'/name,workspace/name)
        output=self.root/'probe.json'
        argv=[str(HERE/'runtime_probe.py'),'--workspace',str(workspace),'--manifest',str(MANIFEST),'--output',str(output)]
        for endings,expected in (('LF',0),('CRLF',0),('real_edit',1)):
            for path in workspace.rglob('*'):
                if path.is_file():
                    content=path.read_bytes().replace(b'\r\n',b'\n')
                    path.write_bytes(content.replace(b'\n',b'\r\n') if endings=='CRLF' else content)
            if endings=='real_edit':
                path=workspace/'ACCESS_POLICY.md'
                path.write_bytes(path.read_bytes()+b'changed')
            with patch.object(sys,'argv',argv),patch('socket.create_connection',side_effect=OSError('SIMULATED blocked')),patch('socket.getaddrinfo',side_effect=OSError('SIMULATED DNS blocked')):
                with self.assertRaises(SystemExit) as status:
                    runpy.run_path(str(HERE/'runtime_probe.py'),run_name='__main__')
            self.assertEqual(status.exception.code,expected)
            self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['passed'],expected==0)

if __name__=='__main__':
    unittest.main(verbosity=2)
