import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sync_skill_mirrors",ROOT/"tools/sync_skill_mirrors.py")
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class MirrorPortabilityTests(unittest.TestCase):
 def test_repo_links_healthy(self):
  errors,count=mod.sync(ROOT,"check")
  self.assertFalse(errors,errors)
  self.assertEqual(count,33)
 def test_copy_mode_portable_and_drift_blocked(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   source=root/".agents/skills/demo"
   (source/"references").mkdir(parents=True)
   (source/"SKILL.md").write_text("---\nname: demo\ndescription: test\n---\n")
   (source/"references/info.md").write_text("original")
   errors,count=mod.sync(root,"copy")
   self.assertFalse(errors,errors)
   self.assertEqual(count,3)
   errors,_=mod.sync(root,"check")
   self.assertFalse(errors)
   (root/".claude/skills/demo/references/info.md").write_text("drift")
   errors,_=mod.sync(root,"check")
   self.assertTrue(any("drifted" in e for e in errors))
   errors,_=mod.sync(root,"copy")
   self.assertTrue(errors)  # never clobber edits
 def test_symlink_restore(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   source=root/".agents/skills/demo";source.mkdir(parents=True)
   (source/"SKILL.md").write_text("---\nname: demo\ndescription: demo\n---\n")
   err,_=mod.sync(root,"symlink")
   self.assertFalse(err,err)
   self.assertTrue((root/".pi/skills/demo").is_symlink())
   err,_=mod.sync(root,"check")
   self.assertFalse(err,err)
if __name__=="__main__": unittest.main()
