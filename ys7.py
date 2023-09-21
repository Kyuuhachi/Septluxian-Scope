import read
import dataclasses as dc
from pathlib import Path

def parse_expr(f: read.Reader):
	ops = []
	while True:
		op = f.u16()
		match op:
			case 1: ops.append("!=")
			case 5: ops.append("%")
			case 6: ops.append("+")
			case 9: ops.append(">")
			case 10: ops.append(">=")
			case 12: ops.append("<=")
			case 13: ops.append("<")
			case 14: ops.append("==")
			case 16: ops.append("&&")
			case 17: ops.append("&")
			case 18: ops.append("||")
			case 26: ops.append(f.u32())
			case 27: ops.append(f.f32())
			case 29: break
			case 31: ops.append("FLAG")
			case 32: ops.append("WORK")
			case 35: ops.append("ALLITEMWORK")
			case 41: ops.append("rand()")
			case 53: ops.append("IsPartyIn")
			case 66: ops.append("0-")
			case _:
				print(op)
				read.dump(f.data)
				ops.append("-error-")
				return ops
	assert not f.remaining
	return ops

def parse_function(f: read.Reader, length: int):
	end = f.pos + length
	insns = []
	has_error = False
	while f.pos < end:
		op = f.u16()
		a = None
		match op:

			case 0x8000:   name = "return"
			case 0x8001: name = "LoadArg"
			case 0x8006: name = "ChangeAnimation"
			case 0x8007: name = "Message"
			case 0x8008: name = "Wait"
			case 0x8009: name = "WaitFade"
			case 0x800A: name = "WaitMenu"
			case 0x800B: name = "SetChrPos"
			case 0x800D: name = "MoveTo"
			case 0x8013: name = "Turn"
			case 0x801B: name = "MoveZ"
			case 0x801F: name = "MoveCameraAt"
			case 0x8020: name = "RotateCamera"
			case 0x8021: name = "ChangeCameraZoom"
			case 0x8022: name = "ChangeCameraPers"
			case 0x8023: name = "ChangeCameraElevation"
			case 0x8024: name = "ChangeCameraDistance"
			case 0x8025: name = "MoveCamera"
			case 0x8026: name = "SaveCamera"
			case 0x8027: name = "RestoreCamera"
			case 0x8028: name = "SetStopFlag"
			case 0x8029: name = "ResetStopFlag"
			case 0x802A: name = "SetChrInfoFlag"
			case 0x802B: name = "ResetChrInfoFlag"
			case 0x802C: name = "SetFlag"
			case 0x802D: name = "SetChrWork"
			case 0x802E: name = "SetWork"
			case 0x802F: name = "JoinParty"
			case 0x8031: name = "SeparateParty"
			case 0x8032: name = "FadeOut"
			case 0x8033: name = "FadeIn"
			case 0x8034: name = "CrossFade"
			case 0x8035: name = "MenuReset"
			case 0x8036: name = "MenuAdd"
			case 0x8037: name = "MenuOpen"
			case 0x8038: name = "MenuClose"
			case 0x8039: name = "YesNoMenu"
			case 0x803D: name = "PlaySE"
			case 0x803F: name = "SetName"
			case 0x8040: name = "TalkMes"
			case 0x8041: name = "Message2"
			case 0x8042: name = "WaitPrompt"
			case 0x8044: name = "Portrait_Load"
			case 0x8045: name = "Portrait_Unload"
			case 0x8046: name = "Portrait_Create"
			case 0x8047: name = "Portrait_Close"
			case 0x8048: name = "Portrait_Anime"
			case 0x804E: name = "ExecuteCmd"
			case 0x804F: name = "ExecuteFunc"
			case 0x8050: name = "WaitThread"
			case 0x8054: name = "EventCue"
			case 0x8056: name = "HP_Recover"
			case 0x8058: name = "SP_Recover"
			case 0x805C: name = "SetCameraZPlane"
			case 0x805D: name = "ResetCameraZPlane"
			case 0x806A: name = "LookChr"
			case 0x806F: name = "MapHide"
			case 0x8070: name = "MapAnime"
			case 0x8079: name = "ChangeItemSlot"
			case 0x807A: name = "DeleteItem"
			case 0x807B: name = "GetItem"
			case 0x8080:   name = "if"
			case 0x8081:   name = "elif"
			case 0x8082:   name = "else"
			case 0x8085:   name = "goto"
			case 0x8087:   name = "endif"
			case 0x808B: name = "ResetFollowPoint"
			case 0x808C: name = "ResetPartyPos"
			case 0x808E: name = "EarthQuake"
			case 0x808F: name = "SetLevel"
			case 0x8090: name = "EquipWeapon"
			case 0x8091: name = "EquipArmor"
			case 0x8092: name = "EquipShield"
			case 0x8093: name = "EquipAccessory"
			case 0x8097: name = "SetCheckPoint"
			case 0x8099: name = "WarpMenu"
			case 0x809B: name = "DestroyObj"
			case 0x809C: name = "GetSkill"
			case 0x809D: name = "SetSkillShortCut"
			case 0x80A1: name = "AddEX"
			case 0x80A2: name = "SetPartyMember"
			case 0x80A3: name = "SavePartyMember"
			case 0x80A4: name = "RestorePartyMember"
			case 0x80A5: name = "SetEventPartyChr"
			case 0x80A6: name = "LoadEventPartyChr"
			case 0x80A7: name = "ReleaseEventPartyChr"
			case 0x80AA: name = "ResetCameraObserver"
			case 0x80C1: name = "CopyStatus"
			case 0x80C4: name = "EmotionEx"
			case 0x80C6: name = "StopSE"
			case 0x80C8: name = "SetFog"
			case 0x80C9: name = "GetItemMessageExPlus"
			case 0x80CC: name = "CampMenu"
			case 0x80D5: name = "SetMapMarker"
			case 0x80D6: name = "DelMapMarker"
			case 0x80DD: name = "Portrait_SetKoma"
			case 0x80E6: name = "HP_ORecover"
			case 0x80F1: name = "SetDiaryFlag"
			case 0x80F4: name = "Set3DParticle"
			case 0x80F5: name = "Change3DParticleParam"
			case 0x80F7: name = "Stop3DParticle"
			case 0x80F8: name = "SetOverlay"
			case 0x80F9: name = "StopOverlay"
			case 0x80FB: name = "ChrNodeHide"
			case 0x80FD: name = "RollCamera"
			case 0x8100: name = "SetMapViewPos"
			case 0x8101: name = "ResetTracks"
			case 0x8103: name = "StartZapping"
			case 0x8104: name = "StopZapping"
			case 0x8105: name = "ChrLightState"
			case 0x8108: name = "CreateLight"
			case 0x810A: name = "SetLightRadius"
			case 0x810B: name = "SetLightColor"
			case 0x810C: name = "CureAll"
			case 0x8112: name = "FadeBGM"
			case 0x8114: name = "Timer"
			case 0x8117: name = "PlayVoice"
			case 0x811C: name = "GetTrophy"
			case 0x8120: name = "ChangeSubAnimation"
			case 0x8121: name = "SubAnimationMode"
			case 0x8122: name = "OpenMinimap"
			case 0x8126: name = "TalkPopup"
			case 0x8127: name = "MenuType"
			case 0x8129: name = "SetDoF"
			case 0x812A: name = "SetDoFFocus"
			case 0x812B: name = "SetGlare"
			case 0x812C: name = "SetFogLightFade"
			case 0x812D: name = "SetMapLightColor"
			case 0x812E: name = "SetMapLightVec"
			case 0x812F: name = "SetMapShadowColor"
			case 0x8130: name = "SetMapChrColor"
			case 0x8131: name = "SetChrLightRatio"
			case 0x8132: name = "SetWeaponLevel"
			case 0x8133: name = "WaitCloseWindow"
			case 0x8134: name = "LookRotateLimit"
			case 0x8135: name = "LookRoll"
			case 0x8136: name = "LookSpd"
			case 0x8137: name = "FixCamera"
			case 0x8138: name = "ResetMapParam"
			case 0x8139: name = "SetName2"
			case 0x813A: name = "OpenMessage"
			case 0x813B: name = "CloseMessage"
			case 0x813C: name = "WaitCloseMessage"
			case 0x813D: name = "SetWorldMapping"
			case 0x813E: name = "SetMotSpd"
			case 0x813F: name = "KeyAnimeCreate"
			case 0x8140: name = "KeyAnimeSet"
			case 0x8142: name = "KeyAnimeChara"
			case 0x8142: name = "KeyAnimeChara"
			case 0x8143: name = "KeyAnimeRelease"
			case 0x8143: name = "KeyAnimeRelease"
			case 0x8145: name = "ActiveVoiceStart"
			case 0x8146: name = "ActiveVoiceStop"
			case 0x8147: name = "InterceptStart"
			case 0x8148: name = "Intercept"
			case 0x8149: name = "JoinNPC"
			case 0x814C: name = "InterceptStop"
			case 0x814D: name = "EquipCostume"
			case 0x814F: name = "CallFunc"
			case 0x8155: name = "DelCheckPoint"
			case 0x8158: name = "SoundEfx"
			case 0x815A: name = "SaveEventState"
			case 0x815B: name = "RestoreEventState"
			case 0x815D: name = "InterceptResume"
			case 0x8160: name = "PitchChr"
			case 0x8161: name = "RollChr"
			case 0x8164: name = "SetDiaryCharaFlag"
			case 0x8165: name = "ItemBackup"
			case 0x816B: name = "Portrait_SS"
			case 0x816E: name = "SetDiaryShopFlag"
			case 0x817D: name = "MenuEnable"
			case 0x817F: name = "GetTrophyDirect"
			case 0x8180: name = "DelMapMarkerAll"

			case 0x82DD: name = "  int"; a = f.i32()
			case 0x82DE: name = "  float"; a = f.f32()
			case 0x82DF: name = "  string"; a = f[f.u32()].decode("cp932")
			case 0x82E0: name = "  expr"; a = parse_expr(f.sub(f.u32()))

			case 0x2020:
				name = "  text";
				nlines, nbytes = f.u32(), f.u32()
				starts = [f.u32() for _ in range(nlines)]
				text = f[nbytes]
				a = [
					text[a:b].decode("cp932")
					for a, b in zip(starts, starts[1:] + [nbytes])
				]

			case v:
				has_error = True
				name = f"\x1B[31m{v:04X}\x1B[m"
				print("\n" + " "*21 + f"-error 0x{op:X}", end=" ")
				read.dump(f[min(end - f.pos, 48)])
				raise ValueError
		if a is not None:
			print(" "+repr(a), end="")
		else:
			print("\n" + " "*21, end="")
			print(f"{name}", end="")
		insns.append((name, a))
	print()
	# if has_error: raise ValueError
	# read.dump(f[min(length, 48)])

def parse_ys7_scp(f: read.Reader):
	f.check(b"YS7_SCP")
	f.check_u32(0)
	unk = f[9]

	for _ in range(f.u32()):
		name = f[32].rstrip(b"\0").decode("cp932")
		length = f.u32()
		start = f.u32()
		print(name)
		parse_function(f.at(start), length)

f = read.Reader(open("/home/large/kiseki/ys8/script/test.bin", "rb").read())
parse_ys7_scp(f)
# for f in sorted(Path("/home/large/kiseki/nayuta/script/").glob("*.bin")):
# 	# print(f)
# 	parse_ys7_scp(read.Reader(f.read_bytes()))
