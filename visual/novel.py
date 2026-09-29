import base64
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Quiet Hours", page_icon="🕯️", layout="centered")

# ----------------------------------------------------------------------------
# QUIET HOURS — a horror romance in six nights
#
# You hunt monsters for the Ordinance of Quiet Hours.
# Harthur is a bookbinder who is not a man, and who has started counting
# the hours between your visits.
#
# Two problems run at once. The first is whether any of this is happening:
# the lamp that shows you the truth burns through your own eyes, so nothing
# you see will ever survive being written down. The second is that every
# time you try to prove it, he feels it, and something in him closes.
#
# Debts, openly: George Orwell's NINETEEN EIGHTY-FOUR (the total ledger, the
# interrogation that wants a word rather than a fact, the Quiet Room, the
# colleague informed on by his own wife); Franz Kafka's THE METAMORPHOSIS
# (the voice going first, the morning the body stops being yours, the iron
# grown over in a back that cannot reach it, the sweeping-out afterward); and
# Fyodor Dostoevsky's NOTES FROM UNDERGROUND (self-cross-examination and the
# need to make a defense even when nobody has accused you).
# ----------------------------------------------------------------------------

INITIAL_STATS = {"harthur": 0, "pull": 0, "suspicion": 0, "change": 1, "proof": 0}

STAT_LABELS = {
    "harthur": "Harthur",
    "pull": "The Pull",
    "suspicion": "Ordinance Interest",
    "change": "Conformity of the Body",
    "proof": "What You Can Prove",
}

STAT_ORDER = ["harthur", "pull", "proof", "suspicion", "change"]

STAT_BANDS = {
    "harthur": [
        (0, "He is being polite"),
        (3, "He is paying attention"),
        (7, "He is keeping you"),
        (11, "He will not be able to let go"),
    ],
    "pull": [
        (0, "You are doing your job"),
        (3, "You are making excuses"),
        (6, "You keep going back"),
        (9, "You want to be taken"),
    ],
    "proof": [
        (0, "Nothing at all"),
        (1, "Only your own eyes"),
        (3, "Marks on you"),
        (6, "Something they would have to answer"),
    ],
    "suspicion": [
        (0, "Unremarkable"),
        (2, "Noted"),
        (5, "Flagged"),
        (8, "Scheduled"),
    ],
    "change": [
        (0, "Within tolerance"),
        (2, "Irregular"),
        (4, "Reportable"),
        (6, "Disposable"),
    ],
}

# Ceilings are the highest each stat can actually reach on any route, so the
# sidebar bars never pin before the end.
STAT_MAX = {"harthur": 19, "pull": 18, "suspicion": 8, "change": 10, "proof": 11}

ENDING_ORDER = [
    "e_amended",
    "e_mire",
    "e_struck",
    "e_clean_report",
    "e_quiet_room",
    "e_mercy",
    "e_verminous",
    "e_ash",
    "e_nosuchman",
]


# ----------------------------------------------------------------------------
# STATE
# ----------------------------------------------------------------------------
def fresh_run():
    st.session_state.scene = "s_open"
    st.session_state.stats = dict(INITIAL_STATS)
    st.session_state.flags = set()
    st.session_state.log = []
    st.session_state.decision_checkpoints = []
    st.session_state.page = 0


if "started" not in st.session_state:
    st.session_state.started = False
if "name" not in st.session_state:
    st.session_state.name = "Tobias Calloway"
if "endings_found" not in st.session_state:
    st.session_state.endings_found = set()
# The journal persists across playthroughs. So does the Registry.
if "journal" not in st.session_state:
    st.session_state.journal = set()
if "journal_new" not in st.session_state:
    st.session_state.journal_new = set()
if "journal_show_new" not in st.session_state:
    st.session_state.journal_show_new = set()
if "journal_page" not in st.session_state:
    st.session_state.journal_page = 0
if "decision_checkpoints" not in st.session_state:
    st.session_state.decision_checkpoints = []
# One paragraph to a page. This is the page we are on.
if "page" not in st.session_state:
    st.session_state.page = 0
if "scene" not in st.session_state:
    fresh_run()


def stats():
    return st.session_state.stats


def flags():
    return st.session_state.flags


# ----------------------------------------------------------------------------
# THE JOURNAL — entries unlock as things appear in the story.
#
# Two registers each: "official" is the Ordinance's own text, rendered as
# paper. "note" is what the officer has written underneath it, which is
# usually the same fact with the comfort taken out.
# ----------------------------------------------------------------------------
JOURNAL_CATS = [
    "Issue",
    "The Ordinance",
    "The Registry",
    "The City",
    "Persons",
    "The Change",
]

JOURNAL = {
    # -------------------------------------------------------------- Issue
    "nail": {
        "term": "The Nail",
        "cat": "Issue",
        "official": "ORDINANCE ISSUE, PATTERN 3\nIron, nine inches, unhafted. One per sworn officer.\nNot to be sharpened, exchanged, decorated, or mourned.",
        "note": "It is cold in a way that iron should not be cold. It does not warm in the hand. Eleven years, and it has never once warmed in the hand.",
    },
    "lamp": {
        "term": "The Lamp",
        "cat": "Issue",
        "official": "ORDINANCE ISSUE, PATTERN 1\nBurns without wick or oil. Renders the true shape beneath a held\nform. Serviceable for the working life of the bearer.",
        "note": "It does not shine. It arrives. And the light is not in the lamp — it is in my eyes, which is the whole of the problem, because it means nothing I have ever seen with it can be shown to anybody else.",
    },
    "draught": {
        "term": "The Draught",
        "cat": "Issue",
        "official": "One thimble, weekly, without exception. Confers lamp-sight.\nRefusal is a disposition.\nSee schedule 9 for reportable effects.",
        "note": "Schedule 9 is four pages long. Page two is headed VISUAL AND AUDITORY IRREGULARITY and it runs to sixty-one entries. I have read it now. I wish I had read it at seventeen and I am glad I did not.",
    },
    "badge": {
        "term": "The Badge",
        "cat": "Issue",
        "official": "Brass. Bears no name. The authority resides in the badge and not\nin the bearer.",
        "note": "That sentence is printed to reassure the public. Read it again as the bearer.",
    },
    # ------------------------------------------------------ The Ordinance
    "ordinance": {
        "term": "The Ordinance of Quiet Hours",
        "cat": "The Ordinance",
        "official": "Constituted to identify, register and dispose of non-human persons\nresident in the city. Its authority derives from the Registry.\nThe Registry derives its authority from the Ordinance.",
        "note": "Nobody has ever been able to explain that second pair of sentences to me, and everybody agrees that they are correct.",
    },
    "quiet_hours": {
        "term": "The Quiet Hours",
        "cat": "The Ordinance",
        "official": "The six hours of the night, numbered. The Ordinance conducts its\nbusiness within them by preference.",
        "note": "The third is the one they favour for a collection. It is the hour at which the body least wants to be a witness. They know that. It is in the training manual, on page nine, as a recommendation.",
    },
    "disposition": {
        "term": "Disposition",
        "cat": "The Ordinance",
        "official": "Any determination entered against a name.\nPermitted values: see schedule 4.",
        "note": "A butcher's word. It means only: separate at the natural place. It is also what they call having an opinion, which tells you everything about how this city is put together.",
    },
    "disposal": {
        "term": "A Public Disposal",
        "cat": "The Ordinance",
        "official": "Where a subject is taken in the open, disposal may proceed in the\nopen. Public confidence is a legitimate objective.",
        "note": "Marrow Street, a Tuesday, four in the afternoon. Two hundred people, and a man selling hot drinks off a tray. A woman behind me lifted her boy onto her shoulders so that he could see over the hats, and she did it the way you would at a parade. They are frightened all the time, these people. This is the one hour in the year when somebody hands them the other end of it.",
    },
    "third_nail": {
        "term": "Third Nail",
        "cat": "The Ordinance",
        "official": "Field rank. Below Second Nail, above intake. Carries a district,\na lamp, and personal disposal discretion.",
        "note": "It sounds like a rank. It is a position in a queue.",
    },
    "nail_school": {
        "term": "The Nail School",
        "cat": "The Ordinance",
        "official": "Intake at seventeen. Two years. Officers of the Ordinance are not\nrecruited. They are raised.",
        "note": "They teach you to put iron through a thing's eye and they teach you the schedules by number. They do not teach you to read the schedules, which turns out to have been the only part that was ever going to save anybody.",
    },
    "quiet_room": {
        "term": "The Quiet Room",
        "cat": "The Ordinance",
        "official": "White. Warm. Drained. Attendance is not a punishment and is not\nto be described as one in any document.",
        "note": "Nobody comes out of it hurt. That is not a mercy, that is the entire method, and it took them four hundred years to arrive at it.",
    },
    # -------------------------------------------------------- The Registry
    "registry": {
        "term": "The Registry",
        "cat": "The Registry",
        "official": "Ninety thousand names. The complete civil record of the city.\nA person is a name in the Registry.",
        "note": "That last line is not a figure of speech, it is the legal definition. Which means the book does not describe who is a person. The book decides.",
    },
    "civil_green": {
        "term": "Civil Green",
        "cat": "The Registry",
        "official": "Binding colour reserved to the civil record. Ordinance green is\nreserved to internal document. Confusion of the two is an offence.",
        "note": "He has a wall of civil green in his front room. They send it to him to be mended. For twenty years they have been couriering him the thing itself, in crates, with a docket.",
    },
    "amendment": {
        "term": "Amendment",
        "cat": "The Registry",
        "official": "Correction of the civil record. Permitted to clerks of the second\ngrade and above, under seal.",
        "note": "A scraper, a steady hand, forty minutes. The name goes down into the grain, the page goes back into the book, and nobody ever notices, because nobody reads a ledger to find out what isn't in it.",
    },
    "hunter_roll": {
        "term": "The Hunter Roll",
        "cat": "The Registry",
        "official": "ORDINANCE GREEN — INTERNAL\nEvery nail sworn in this city for forty years.\nName, intake, district, disposition.",
        "note": "Four hundred and eleven of us. Every one sworn at seventeen. Not one entry in the column says RETIRED. And this one I can hold. This one is paper.",
    },
    "duplicates": {
        "term": "The Duplicate",
        "cat": "The Registry",
        "official": "Since the fire of '09 every civil record is copied nightly to the\nsub-annex at Calder Yard. Schedule 2, clause 1.",
        "note": "Printed in the ordinances I swore an oath to enforce. I had not read it. Nobody reads them. Reading them is a disposition.",
    },
    # ------------------------------------------------------------ The City
    "vantage": {
        "term": "Vantage",
        "cat": "The City",
        "official": "The city. Population ninety thousand, as recorded.",
        "note": "As recorded.",
    },
    "ashmoor": {
        "term": "Ashmoor Row",
        "cat": "The City",
        "official": "Tenement district, east bank. Eleven flats to a stair.",
        "note": "Third floor, the twelfth of a cold March, twenty years ago. I have held this district for two years. I asked for it. I have never once been able to tell anybody why.",
    },
    "chalk": {
        "term": "The Chalk",
        "cat": "The City",
        "official": "No entry. The Ordinance does not chalk doors and has issued four\nnotices to that effect.",
        "note": "A short vertical stroke at shoulder height, left of the latch. Neighbours do it. It means: we have discussed you. By the time we arrive the mark is usually a week old and everyone on that stair has walked past it twice a day and said nothing, including the ones who are fond of her, including the ones who will cry about it afterward.",
    },
    "informers": {
        "term": "The Queue",
        "cat": "The City",
        "official": "Public information is received at the front counter between the\neighth and eleventh hours. No appointment is necessary.",
        "note": "It goes out of the door and along the railings. They bring their hats. Some of them bring their children, and hold them by the hand, and shush them. Nobody in that queue thinks of themselves as an informer. Every one of them thinks of themselves as careful.",
    },
    "listening": {
        "term": "The Listening",
        "cat": "The City",
        "official": "Brass ear-grille, one to each habitable room, to be kept clear at\nall times. Obstruction is a capital matter.",
        "note": "His is packed solid with candle wax and grey wool and he has not hidden it. He says it whistles in the winter. That is the whole of his defence, and he offers it the way you would explain a stain on a cuff.",
    },
    "mire": {
        "term": "The Mire",
        "cat": "The City",
        "official": "Sub-structure. Flood works, disused. Not surveyed, not serviced,\nand not, in the strict sense, within the city.",
        "note": "No grilles down there. No book. The water is warm, which is the first thing nobody ever tells you about it.",
    },
    "tallow_yard": {
        "term": "Tallow Yard",
        "cat": "The City",
        "official": "Registry house. One long room. Four hundred years of paper.\nSealed automatically in the event of fire.",
        "note": "That last clause is in schedule 2 as well, four lines below the one about the duplicates. I have now read both of them.",
    },
    "calder_yard": {
        "term": "Calder Yard",
        "cat": "The City",
        "official": "Sub-annex. Also: a stair, a laundry, and an address which no\nlonger means anything to anybody living.",
        "note": "Somebody was issued iron on that stair a very long time ago and was standing on the wrong landing when he used it. He walks past the laundry on Thursdays.",
    },
    # ------------------------------------------------------------- Persons
    "harthur": {
        "term": "Harthur",
        "cat": "Persons",
        "official": "No surname of record. Binder — ledgers, civil record, Ordinance\nrepair. Registry flag 44-118-C. Disposition: pending.",
        "note": "He opened the door before I had finished knocking and stepped aside before I asked. People do not invite the Ordinance in. People are entered.",
    },
    "crow": {
        "term": "Warden Ilsabet Crow",
        "cat": "Persons",
        "official": "Warden, Ashmoor and Calder. Four commendations. The city's monster\nfigure has fallen in every year of her service.",
        "note": "She has never once packed her grille. She asks questions she already holds the answers to, because a thing said aloud in that room becomes true, and a thing left unsaid stays only a fact.",
    },
    "rell": {
        "term": "Rell Oduya",
        "cat": "Persons",
        "official": "Second Nail, intake '29. Ashmoor beat. Clean file.",
        "note": "Cleans his lamp with his shirt-tail, in breach of four separate ordinances, in the one corner of the yard where the grille has been broken for six years and everybody knows it is broken and nobody has reported it.",
    },
    "sollers": {
        "term": "Sollers",
        "cat": "Persons",
        "official": "Third Nail, intake '34. Assigned in assistance.",
        "note": "Drinks his Draught in front of people. Carries my file in a satchel he never puts down. That is not a partner. That is a second opinion.",
    },
    "anselm": {
        "term": "Mrs. Anselm",
        "cat": "Persons",
        "official": "Flat Nine, Ashmoor Row. Seventy-one years. Feeds stray animals.\nDisposition: entered.",
        "note": "She pinned her hair before she opened the door, because she was raised properly. She asked what she had done. Nobody told her. There was chalk on that door and it was eight days old.",
    },
    "maro": {
        "term": "Maro",
        "cat": "Persons",
        "official": "Ashmoor Row, third floor. Collected the twelfth of a cold March,\ntwenty years past. Entry intact.",
        "note": "Three shelves along. Perfect condition, in a warm room two streets from where they took her. Never damaged, so never sent out for mending, so never reached. There is no design in it. That is the part I cannot get past.",
    },
    # ---------------------------------------------------------- The Change
    "seam": {
        "term": "The Seam",
        "cat": "The Change",
        "official": "No entry.",
        "note": "Third vertebra to the small of the back. It opens in the night and closes before the bell, and what it leaves on the sheet is dark and smells of almonds and dries to a crust you can lift away in one piece. I cannot see it. It is on my back. I have to take somebody's word for my own body now, and there is exactly one person in this city I could ask.",
    },
    "the_face": {
        "term": "The Face",
        "cat": "The Change",
        "official": "No entry.",
        "note": "Not a mask and not a disguise. It is held, the way you hold a breath, and coming out of it is not a removal. It is a birth, and it is as wet as one, and he puts both hands flat on the table first because he knows exactly how much of it there is going to be.",
    },
    "almonds": {
        "term": "Almonds",
        "cat": "The Change",
        "official": "No entry.",
        "note": "I put it down to damp on the first night, because a stairwell is allowed to smell of something and a man is not. It was never the stairwell. It is what he is made of, and after the fourth night I could find it on my own hands, and I did not wash them.",
    },
    "thirst": {
        "term": "The Pull",
        "cat": "The Change",
        "official": "No entry. Schedule 9 has no heading for this.",
        "note": "Sixty-one entries on page two and not one of them is: the officer will begin to want it. Not the sight. The thing itself. I have been up those stairs eleven times now and I have stopped pretending any of them were the job.",
    },
}


def unlock(keys):
    for key in keys:
        if key in JOURNAL and key not in st.session_state.journal:
            st.session_state.journal.add(key)
            st.session_state.journal_new.add(key)


# ----------------------------------------------------------------------------
# ENDING RESOLVERS
#
# The last choice picks a door. The six nights pick the room.
# Proof is checked first everywhere: if you never came away with anything
# that would survive being written down, there is nothing at the end of this
# that can be shown to have happened.
# ----------------------------------------------------------------------------
def resolve_door():
    s, f = stats(), flags()
    if s["proof"] <= 1:
        return "e_nosuchman"
    if s["change"] >= 6:
        return "e_verminous"
    if "drew_iron" in f or s["harthur"] <= 3:
        return "e_mercy"
    return "e_quiet_room"


def resolve_run():
    s = stats()
    if s["proof"] <= 1:
        return "e_nosuchman"
    # "Disposable" on the body meter is the gate for both of these; whether
    # he reaches you in the water is what decides which one you get.
    if s["change"] >= 6 and s["harthur"] >= 7:
        return "e_mire"
    if s["change"] >= 6:
        return "e_verminous"
    if s["harthur"] >= 9 and s["pull"] >= 7:
        return "e_amended"
    return "e_clean_report"


def resolve_burn():
    s = stats()
    if s["proof"] <= 1:
        return "e_nosuchman"
    if s["harthur"] >= 7:
        return "e_struck"
    return "e_ash"


# ----------------------------------------------------------------------------
# THE STORY
#
# Text blocks are (kind, body) pairs. "n" is narration, "doc" is an Ordinance
# paper, "!" is a beat set apart. Anything else is a speaker name; "you" is
# replaced with the player's name.
# ----------------------------------------------------------------------------
SCENES = {
    # ------------------------------------------------------------------ I
    "s_open": {
        "act": "Night One",
        "title": "The Knock",
        "journal": [
            "ordinance", "vantage", "nail", "lamp", "registry",
            "disposition", "quiet_hours", "ashmoor", "harthur", "disposal",
        ],
        "text": [
            ("n", "The Ordinance issues you three things: an iron nail nine inches long, a lamp that burns without wick or oil, and a name that is not yours. The name belongs to whoever carries the badge. Tonight that is you."),
            ("n", "You come to Ashmoor Row the long way, because Marrow Street is closed, because there is a disposal on."),
            ("n", "Two hundred people, perhaps. More. They have been standing since the afternoon and the mood is not what the pamphlets say it is — it is not grim and it is not dutiful. There is a man selling hot drinks off a tray. A woman behind you lifts her boy onto her shoulders so that he can see over the hats, and she does it the way you would at a parade."),
            ("n", "What is in the road has four working limbs and three that are not limbs, and it is making a sound through a throat that was, until about an hour ago, doing an excellent impression of a grocer's on Tench Lane. Second Nail Hollis is taking his time, because taking his time is the point, because public confidence is a legitimate objective and it is written down as one."),
            ("!", "The boy on his mother's shoulders is perhaps five. He is not crying. He is rapt."),
            ("n", "They are frightened all the time, these people. Every one of them has lain awake wondering about a neighbour. This is the one afternoon in the year when somebody hands them the other end of it, and you have never once been able to blame them for taking it, and you have never once been able to watch the whole way through."),
            ("n", "You go the long way. The flag came down from Registry at the fourth quiet hour."),
            ("doc", "REGISTRY FLAG 44-118-C\nDISTRICT: Ashmoor Row, Flat Six\nSUBJECT: HARTHUR, no surname of record\nTRADE: binder — ledgers, civil record, Ordinance repair\nANOMALY: reflective goods purchased, eleven years: NIL\nDISPOSITION: observe, verify, dispose"),
            ("n", "Dispose is a word the Ordinance uses the way a butcher uses joint. It means only: separate at the natural place."),
            ("n", "Four flights. The stairwell smells of almonds and wet stone, which you file away as damp, because the alternative is that a building can be nervous."),
            ("n", "The door opens on a thin man with ink to the second knuckle and a face that seems, for about a quarter of a second, to still be deciding where to put itself."),
            ("n", "His hands are wet. You take it for glue — a binder's hands are always wet with something — and then he turns one over to push his hair back, and you see that it is coming from under the nailbeds, all five, steadily, dark and thin and not a colour that blood is permitted to be."),
            ("n", "He follows your eyes down. He looks at his own hand with an expression of mild social embarrassment, as though he has been caught with a button undone."),
            ("Harthur", "You're early. Or I'm late. One of us has done something wrong to the evening."),
        ],
        "choices": [
            {
                "label": "Show him the badge. Say the words.",
                "detail": "Protocol. Logged contact. The Ordinance loves a man who files.",
                "effects": {"harthur": -1, "suspicion": -1},
                "outcome": [
                    ("n", "You hold up the brass and recite the formula, and something behind his eyes packs itself away very neatly, like a man folding a letter he has decided not to send."),
                    ("Harthur", "Of course. Yes. Everyone is so busy this time of year."),
                    ("n", "He wipes his hands down the front of his apron as he turns, and the smear it leaves is black and thick and about nine inches long."),
                    ("!", "When you look again — and you look almost at once, you look within four seconds — the apron is clean."),
                ],
                "next": "s_tea",
            },
            {
                "label": "Tell him you're the new tenant upstairs.",
                "detail": "A lie. Unlogged. Small. The small ones are how people start.",
                "effects": {"harthur": 1, "pull": 1, "suspicion": 1},
                "outcome": [
                    ("n", "The lie comes out of you smoothly and without permission, and you understand, hearing it, that some part of you decided on the stair."),
                    ("Harthur", "Flat Eight. That's the one with the crack shaped like a dog. Come in, then — I'll want to know what you make of the dog."),
                    ("n", "He is bad at being suspicious. He is so bad at it that you spend the first ten minutes looking for the trick, and there is no trick, and that will turn out to be the most frightening thing about him."),
                ],
                "next": "s_tea",
            },
            {
                "label": "Say nothing. Raise the lamp.",
                "detail": "It shows the shape under the face. It burns through your eyes to do it.",
                "effects": {"change": 1, "pull": 1},
                "flags": ["lamp_used"],
                "outcome": [
                    ("n", "The lamp does not shine. It arrives. The landing goes the colour of an old tooth and every shadow in it stands up straight, and for one half of one second the doorway is full."),
                    ("n", "Not full of a man. Full — corner to corner, floor to lintel — of something wet and articulated and folded over on itself perhaps nine times, with the thin man hanging in the middle of it like a coat on a hook."),
                    ("n", "Then it is a landing, and a door, and a bookbinder with ink on his hands."),
                    ("!", "Your eyes are bleeding. Not much. Enough that your knuckle comes away red when you check, and enough that you understand, standing there, that the lamp did that, and that the lamp does that every time, and that nobody at the Nail School ever said so."),
                    ("Harthur", "Ah."),
                    ("Harthur", "Come in and sit down. You've gone a colour. The kettle's on regardless."),
                ],
                "next": "s_tea",
            },
        ],
    },

    "s_tea": {
        "act": "Night One",
        "title": "The Kettle",
        "journal": ["listening", "civil_green", "almonds"],
        "text": [
            ("n", "He steps aside before you ask. That is the first wrong thing. People do not invite the Ordinance in. People are entered."),
            ("n", "Two rooms. A binding press, a glue pot, a wall of ledgers in civil green — the city's own books, out for repair, which means the Registry trusts this man with the machinery of who exists."),
            ("n", "No mirror. No window glass on the inner wall. A kettle of dull tin that gives back nothing at all."),
            ("n", "In the ceiling corner, the brass ear-grille every room in Vantage is required to keep clear. His is packed solid with candle wax and grey wool. He has not hidden it. It is the capital crime of the age and it is sitting up there like a dead wasp."),
            ("Harthur", "It whistles. In the winter. I couldn't sleep."),
            ("n", "He says it the way you would explain a stain. Then he pours."),
            ("n", "And the index finger of his right hand opens."),
            ("n", "It opens along the top, knuckle to nail, the way a pod opens — not a cut, there is no edge to it, the skin simply parts because whatever is underneath has decided that it needs the room. What is underneath is pale and segmented and jointed in three places. It flexes once, and adjusts, and the skin comes back over it and seals without a mark."),
            ("n", "The whole thing takes under two seconds. He does not stop pouring. He does not appear to notice, and you cannot tell whether that is because it did not happen or because it happens forty times a day."),
            ("!", "There is one bead left on the kettle handle. Dark. Beading up rather than soaking in. Still there."),
        ],
        "choices": [
            {
                "label": "Take his wrist before it closes.",
                "detail": "You are trained for this. Confirm the anomaly by touch.",
                "effects": {"harthur": -1, "pull": 1, "proof": 1},
                "flags": ["grabbed"],
                "outcome": [
                    ("n", "You have his wrist before you decide to. It is warm. It is a perfectly ordinary wrist for about a second and a half."),
                    ("n", "Then the whole forearm shifts under your palm — not a muscle moving, a structure moving, several somethings reorganising themselves out of your grip the way a cat moves a paw when you sit on it — and you feel a hard segmented ridge travel up the inside of his arm, wrist to elbow, unhurried, and gone."),
                    ("n", "He does not pull away. He lets you hold on for as long as you want, and that is worse than any amount of pulling away would have been."),
                    ("Harthur", "You can keep it as long as you like. I'd only ask that you drink the tea first — it's the last of the good leaf and I'd hate for this to have wasted it."),
                    ("!", "You felt it. You know exactly what you felt. There is no possible way to write down what you felt."),
                ],
                "next": "s_summons",
            },
            {
                "label": "Wipe the kettle handle. Keep the cloth.",
                "detail": "It is on the tin. It is outside your head. Get it into your pocket.",
                "effects": {"harthur": -3, "proof": 2},
                "flags": ["cloth"],
                "outcome": [
                    ("n", "You take out your handkerchief and you wipe the handle of another man's kettle in his own front room, and you fold it, and you put it away."),
                    ("n", "It is not a subtle thing to have done. He watches the whole of it."),
                    ("n", "And something in him closes. Not anger — you would know what to do with anger. It is a door going quietly to, somewhere three rooms back, and the man left standing in front of you afterward is perfectly pleasant and has gone a very long way away."),
                    ("Harthur", "Of course. You'll want something for the file."),
                    ("Harthur", "Milk?"),
                    ("!", "In your pocket, through the cloth, through the wool of the coat, you can feel that it is still warm. It stays warm for two hours."),
                ],
                "next": "s_summons",
            },
            {
                "label": "Look at the tea. Drink it.",
                "detail": "You did not see anything. There is nothing in the ledger about fingers.",
                "effects": {"harthur": 3, "pull": 1},
                "outcome": [
                    ("n", "You look at the tea. You drink the tea. It is very good tea, and it is the first thing you have swallowed in eleven years that nobody recorded."),
                    ("n", "Across the table something in him lets go by about an inch. He sits down like a man setting down a bag he has been carrying since morning."),
                    ("Harthur", "Thank you."),
                    ("you", "For what?"),
                    ("Harthur", "For the tea. Obviously. What else would it be for."),
                    ("n", "The bead on the handle dries to nothing over the next half hour. You watch it go. You tell yourself that you are being thorough."),
                ],
                "next": "s_summons",
            },
        ],
    },

    # ----------------------------------------------------------------- II
    "s_summons": {
        "act": "Night Two",
        "title": "Warden Crow",
        "journal": ["crow", "rell", "third_nail", "nail_school", "badge", "informers", "draught"],
        "text": [
            ("n", "The queue for the front counter goes out of the door, along the railings, and around into Tench Lane."),
            ("n", "They have brought their hats. A few have brought their children, and hold them by the hand, and shush them. A man near the front has a list — an actual list, on actual paper, four names on it — and he keeps checking it against nothing."),
            ("n", "Not one person in that queue thinks of themselves as an informer. Every single one of them thinks of themselves as careful."),
            ("n", "Inside, the Ordinance house has no windows on the ground floor and a great many on the fifth, which is a way of telling you where the looking is done."),
            ("n", "In the corridor Rell Oduya is cleaning his lamp with his shirt-tail, in breach of four separate ordinances, and it is the most human thing you will see all week."),
            ("Rell", "She's got your stairwell log up. Don't be interesting, {first}. Interesting is a disposition."),
            ("n", "Warden Ilsabet Crow keeps a clean desk, an ear-grille she has never once packed with wool, and your report in front of her."),
            ("!", "You have not written it yet."),
            ("Crow", "Sit. How long since your thimble?"),
            ("n", "It is not the question you came in braced for, and she watches you not have an answer ready."),
            ("Crow", "Schedule nine, page two. Visual and auditory irregularity. Sixty-one entries, and I have signed off on every one of them at some point in my career."),
            ("Crow", "Officers see things. It is not a disgrace and it is not a secret; it is on a printed page in a building you have worked in for eleven years. The ones who go wrong are not the ones who see things, dear. They are the ones who decide that what they saw was owed something."),
            ("n", "She lets that sit for exactly long enough."),
            ("Crow", "Now. Tell me what you found at Ashmoor Row."),
            ("n", "This is the part they teach at the Nail School without ever naming it. She knows. She has the clerk's flag, the stair log, the hour you went up and the hour you came down with tea on your breath."),
            ("n", "She is not asking in order to learn. She is asking you to say it, because a thing said aloud in this room becomes true, and a thing unsaid remains only a fact."),
            ("doc", "A MONSTER IS A THING THE LEDGER HAS NOT YET NAMED.\nMERCY IS MURDER, DEFERRED.\nYOU ARE NOT BEING WATCHED. YOU ARE BEING KEPT."),
        ],
        "choices": [
            {
                "label": "Report him. Flat Six. Everything.",
                "detail": "The finger. The wax in the grille. The blood under the nails. All of it.",
                "effects": {"harthur": -7, "pull": -2, "suspicion": -3},
                "flags": ["reported"],
                "outcome": [
                    ("n", "It takes ninety seconds. You are good at this, and being good at a thing is a kind of anaesthetic."),
                    ("n", "Crow writes nothing down. She already had it written. She simply watches your mouth make the shapes, and when you are finished she nods, once, the way you would nod at a dog that has finally understood the stick."),
                    ("Crow", "Good. You'll lead the disposal. It's important to me that people finish their own sentences."),
                ],
                "next": "s_a_hunt",
            },
            {
                "label": "Tell her the flat was clean.",
                "detail": "A lie, in the room with the grille, to the woman holding your file.",
                "effects": {"suspicion": 3, "pull": 2},
                "outcome": [
                    ("n", "You say it and the room does not change, which is how you know that it has."),
                    ("Crow", "Clean."),
                    ("you", "Clean, Warden."),
                    ("n", "She lets the silence run four seconds past the point of comfort — a technique, not a pause — and then she smiles, and it is a perfectly kind smile, and she writes one short word on your file and turns it face down."),
                    ("Crow", "Then we're both satisfied. Aren't we."),
                    ("!", "You lied to the Ordinance for a man you have known for one night. You spend the walk home trying to make that sentence mean something other than what it means."),
                ],
                "next": "s_b_watched",
            },
            {
                "label": "Give her Flat Nine instead.",
                "detail": "Mrs. Anselm. Seventy-one. Feeds the stray dogs. Talks to her mirror.",
                "effects": {"suspicion": -2, "change": 1, "pull": 1},
                "flags": ["condemned_stranger"],
                "outcome": [
                    ("n", "You hear yourself do it. Flat Nine. Irregular hours, unaccounted meat going out of the back door nightly, conversation held with a reflective surface at length and out loud."),
                    ("n", "Every word of it is true. That is the craft of the thing. You have not lied to the Ordinance once."),
                    ("Crow", "Nine. Not Six."),
                    ("you", "Nine, Warden."),
                    ("n", "She writes it down, and something very small and very far down in your chest goes quietly out, like a lamp in a room nobody was using."),
                ],
                "next": "s_c_stranger",
            },
        ],
    },

    # --------------------------------------------------------- BRANCH A
    "s_a_hunt": {
        "act": "Night Two",
        "title": "The Warrant",
        "journal": ["disposition"],
        "text": [
            ("n", "They give you six nails and a dawn."),
            ("doc", "DISPOSAL ORDER 44-118-C\nEXECUTING OFFICER: {name}, Third Nail\nSUBJECT: HARTHUR, no surname of record\nMETHOD: at officer's discretion\nNOTE: subject is in possession of thirty-one volumes of civil record.\nRECOVER THE BOOKS FIRST."),
            ("n", "Recover the books first. You read that line about nine times. The Ordinance has assessed a man and thirty-one ledgers and has set out its priorities in the order that it means them."),
            ("n", "On the walk back you go along Marrow Street, which has been reopened. They have hosed it. They have not hosed it well — there is a long dark fan of it up the front of the bootmaker's at number eleven, well above the height a hose reaches, and the bootmaker is open and doing trade and has put his boards out underneath it."),
            ("n", "You have until the first quiet hour. Nobody is watching what you do with it, which is not the same as nobody knowing."),
        ],
        "choices": [
            {
                "label": "Lead it clean. Be first through the door.",
                "detail": "If it is going to be done, it should be done by someone who liked him.",
                "effects": {"harthur": -3, "suspicion": -2},
                "flags": ["raid_led"],
                "outcome": [
                    ("n", "You tell yourself the thing hunters tell themselves, which is that a fast hand is a kindness, and you have never once in your life seen it be a kindness, and you tell yourself anyway."),
                ],
                "next": "s_a_raid",
            },
            {
                "label": "Send back a rebound ledger with a note in the spine.",
                "detail": "One word, in glue, under the endpaper. He is a binder. He will find it.",
                "effects": {"harthur": 4, "pull": 2, "suspicion": 2},
                "outcome": [
                    ("n", "You take a green civil volume from the evidence shelf, split the endpaper, write one word, and glue it down under the marbling where only a man who repairs books would ever think to look."),
                    ("!", "RUN."),
                    ("n", "The clerk logs the volume out to you at the eleventh hour and asks no questions, because asking questions is also a disposition."),
                ],
                "next": "s_molt",
            },
            {
                "label": "Misfile the warrant. Wrong district seal.",
                "detail": "It voids for nine days. He will never know you did it.",
                "effects": {"harthur": 1, "pull": 1, "suspicion": 1},
                "outcome": [
                    ("n", "Calder seal instead of Ashmoor. One stamp, a half-inch out of its parish, and the whole apparatus grinds to a polite halt for nine days while somebody senior decides whose fault it is."),
                    ("n", "It is the smallest treason available and you commit it with your hands shaking, which surprises you. You have put a nail through a thing's eye and not shaken."),
                ],
                "next": "s_molt",
            },
        ],
    },

    "s_a_raid": {
        "act": "Night Two",
        "title": "Flat Six, Empty",
        "journal": ["hunter_roll", "draught"],
        "text": [
            ("n", "The door goes in at the first quiet hour and the rooms are warm and there is nobody in them."),
            ("n", "The glue pot is still soft. The press is still clamped on a half-bound volume. A cup on the table, filled, untouched, gone cold in a way that says hours and not minutes."),
            ("n", "There is a great deal of something dark dried into the grain of the workbench, in a spreading shape, the way a thing dries when it has been coming steadily from one fixed point for several hours. Sollers puts two fingers in it and smells them and says that it is glue."),
            ("!", "It is not glue. But you cannot prove that it is not glue, and neither can he, and his opinion is the one that goes in the file."),
            ("n", "He did not run tonight. He has simply been ready for twenty years, and tonight was the night the readiness got used."),
            ("n", "The others sweep the ledgers into crates. You stand at the table, because one book has been left out, squared up, deliberate as a letter."),
            ("n", "It is not civil green. It is Ordinance green, and it is the hunter roll — every nail sworn in this city for forty years, intake and district and disposition — and it has no business in a binder's rooms in any world you were raised to believe in."),
            ("n", "It is open at the disposition column."),
            ("doc", "HOLLIS, T. . . . . . intake '19 . . . disposition: INTERNAL\nADEYEMI, K. . . . . intake '21 . . . disposition: INTERNAL\nMARCH, O. . . . . . intake '22 . . . disposition: INTERNAL\nVASK, E. . . . . . . intake '22 . . . disposition: INTERNAL\nODUYA, R. . . . . . intake '29 . . . disposition: —\nSOLLERS, B. . . . . intake '34 . . . disposition: —"),
            ("n", "Four hundred and eleven hunters in forty years. Every one of them sworn at seventeen. Not one entry in the column says RETIRED."),
            ("n", "And in the margin, in binder's pencil, in a hand that has had exactly one night to decide whether to write it:"),
            ("!", "\"You should know what they are doing to you. — H\""),
        ],
        "choices": [
            {
                "label": "Take it to Warden Crow.",
                "detail": "A personnel document has left the building. That is the whole of your duty.",
                "effects": {"harthur": -3, "suspicion": -1},
                "outcome": [
                    ("n", "You expect something. An explanation, a denial, a bad hour. You have rehearsed all three on the walk over."),
                    ("Crow", "Yes. That's a personnel document. It oughtn't to be out of the building."),
                    ("n", "She squares it on the desk and asks whether you would care to be put forward for Rell Oduya's district, which has come open."),
                    ("you", "Warden. The disposition column."),
                    ("Crow", "I know what's in the column, dear. I signed the better part of it."),
                    ("n", "She says it without any weight at all, the way you would confirm the day of the week, and goes back to the district paperwork, and after a while you realise that you are still standing there and that nobody is going to ask you to leave."),
                ],
                "next": "s_molt",
            },
            {
                "label": "Put it under your coat.",
                "detail": "Thirty-one volumes went out in crates. Let the count be thirty.",
                "effects": {"harthur": 1, "proof": 1},
                "flags": ["has_roll"],
                "outcome": [
                    ("n", "It sits against your ribs all the way down four flights, and it weighs what a ledger weighs, and it weighs considerably more than that."),
                    ("n", "You read it every night that week with the lamp at a low angle, and the shape of the thing comes up out of the page slowly, the way a bruise does."),
                    ("n", "Sworn at seventeen. Disposition at twenty-nine, thirty, thirty-one. A handful at thirty-two. Nobody at all at thirty-three."),
                    ("!", "You are twenty-eight. And this one is paper. Whatever else turns out not to be true, this is paper, and it is under your floorboard, and it will still be paper in the morning."),
                ],
                "next": "s_molt",
            },
            {
                "label": "Hold it in the glue-pot flame.",
                "detail": "Forty years of the arithmetic of your own life. Do not keep it.",
                "effects": {"harthur": 2, "change": 1},
                "outcome": [
                    ("n", "Ordinance green burns badly and stinks, and you stand over it fanning the smoke into the packed ear-grille so that the room cannot hear itself think."),
                    ("n", "It does not help. You had already read the column. That is the trouble with a thing written down — the burning is for you, and you are the one part of it that cannot be got at."),
                    ("n", "Afterwards your hands are black and there is an ache low in your back, at the third vertebra, which you put down to the stairs."),
                    ("!", "It is not the stairs."),
                ],
                "next": "s_molt",
            },
        ],
    },

    # --------------------------------------------------------- BRANCH B
    "s_b_watched": {
        "act": "Night Two",
        "title": "A Second Opinion",
        "journal": ["sollers", "draught", "chalk"],
        "text": [
            ("n", "By morning you have been assigned assistance."),
            ("n", "Sollers. Young, immaculate, drinks his Draught in front of people. He carries your file in a satchel he never puts down and he says sir and ma'am to everyone including the dogs."),
            ("Rell", "That's not a partner, {first}. That's a second opinion."),
            ("n", "Rell says it out of the side of his mouth in the yard, where the grille is broken and everyone knows it is broken and everyone conducts their entire real life within a nine-foot radius of it."),
            ("Rell", "Whatever you've got, put it down. Whatever it is. I mean it kindly."),
            ("n", "On the Ashmoor stair there is now a chalk mark on Flat Nine. A short vertical stroke at shoulder height, left of the latch."),
            ("n", "The Ordinance does not chalk doors. The Ordinance has issued four notices saying so. Neighbours do it, and it means we have discussed you, and by the time anybody official arrives the mark is usually a week old and every person on that stair has walked past it twice a day and said nothing — including the ones who are fond of her, including the ones who will cry about it afterward."),
            ("n", "There is no chalk on Flat Six. You find that you check. You find that you are relieved, and then you stand on the landing for a while being careful about the word relieved."),
        ],
        "choices": [
            {
                "label": "Stay away. Let it cool.",
                "detail": "Nine minutes' walk. You will not walk it. Not this month.",
                "effects": {"harthur": -2, "pull": -1, "suspicion": -1},
                "outcome": [
                    ("n", "Six days. You are exemplary. Sollers writes that you are exemplary and you read it upside down on his knee and feel nothing at all."),
                    ("n", "On the seventh day you take the long way home, past Ashmoor, on the far pavement, and there is a light in Flat Six and a shape at the press working late, and you keep walking at exactly the speed of a person going home."),
                    ("!", "You get four streets. Then you stop, in the dark, by the railings, and you stand there for eleven minutes doing nothing whatsoever, and then you go home."),
                ],
                "next": "s_molt",
            },
            {
                "label": "Bring Rell. Have him look at the man.",
                "detail": "A second pair of eyes that have never had the lamp in them.",
                "effects": {"harthur": -3, "suspicion": -1},
                "flags": ["rell_looked"],
                "outcome": [
                    ("n", "You take Rell up on a pretext about a rebinding, and you stand in that front room for twenty minutes while the two of them talk about damp and the price of calfskin, and you watch Rell watch him, and you wait."),
                    ("n", "Harthur pours. Harthur's hands do nothing whatsoever. Harthur is, for twenty solid minutes, the single most ordinary man in Vantage."),
                    ("Rell", "He's a bookbinder, mate."),
                    ("Rell", "Nice one, too. Bit sad round the eyes. If you've got him flagged for something then you want to be very sure, because there's nothing there, and I've been doing this four years longer than you have."),
                    ("n", "So now you have a second witness, and the second witness saw a bookbinder."),
                    ("!", "Which means one of two things, and you cannot get at either of them, and both of them keep you up: either you are wrong about everything — or he held it, for twenty minutes, on purpose, because you brought somebody."),
                ],
                "next": "s_molt",
            },
            {
                "label": "Go across the roofs, after the third quiet hour.",
                "detail": "Nobody watches the slates. There is nothing up there to watch.",
                "effects": {"harthur": 2, "pull": 3, "change": 1},
                "outcome": [
                    ("n", "Ashmoor and Calder almost touch at the chimney stacks, and you go across the gap without thinking about it, the way you would step over a puddle."),
                    ("n", "You sit down on the wet slate on the other side with your heart going like a bird in a box, and you work out, slowly, with the arithmetic coming in very cold:"),
                    ("!", "The gap is eleven feet."),
                    ("n", "He opens the skylight before you knock on it. He looks at you crouched on his roof in the rain at the third quiet hour, and what crosses his face is not surprise, and it is not fear, and you will spend the rest of the week failing to name it."),
                    ("Harthur", "Come in out of that. Please. Come in out of that now."),
                    ("n", "And going in — wet through, over the sill, into the warm and the almonds and the lamplight — is the single best thing that has happened to you in eleven years, and you know it at the time, which is the part that frightens you."),
                ],
                "next": "s_molt",
            },
        ],
    },

    # --------------------------------------------------------- BRANCH C
    "s_c_stranger": {
        "act": "Night Two",
        "title": "Flat Nine",
        "journal": ["anselm", "chalk"],
        "text": [
            ("n", "There has been chalk on her door for eight days."),
            ("n", "A short vertical stroke at shoulder height, left of the latch. Neighbours do it. It means we have discussed you. Eleven flats on that stair, and every one of them has walked past it twice a day since the ninth, and said nothing, and gone in, and had their tea."),
            ("n", "They come for Mrs. Anselm at the third quiet hour, which is the hour the Ordinance prefers because it is the hour the body least wants to be a witness."),
            ("n", "She comes down in her coat over her nightdress with her hair still pinned, because she pinned it before she opened the door, because she is seventy-one and was raised properly."),
            ("Mrs. Anselm", "Only tell me what I did. Tell me what it was and I'll stop, I'll stop tonight."),
            ("n", "Nobody tells her. This is not cruelty; it is procedure. To name the charge is to hand the accused something to argue with, and the Ordinance does not hold arguments. It holds people."),
            ("n", "The stair comes out to watch. Not all of them, but enough — six or seven, in doorways, in dressing gowns, arms folded. Nobody says anything to her. One man at the top says, to nobody in particular, in a low pleased voice, that he had always thought there was something."),
            ("n", "Two doors up, a light goes on in Flat Six and does not go off again all night."),
        ],
        "choices": [
            {
                "label": "Stand at the window until the wagon turns the corner.",
                "detail": "Make yourself watch the whole of it. Owe it that much.",
                "effects": {"change": 1},
                "outcome": [
                    ("n", "You watch the wagon to the corner and then you watch the corner, which is empty, for a further twenty minutes."),
                    ("n", "There is a taste in your mouth like a coin. You will have it, on and off, for the rest of the story."),
                ],
                "next": "s_molt",
            },
            {
                "label": "Climb to Flat Six and tell him what you did.",
                "detail": "Out loud. In the room with the wax in the grille.",
                "effects": {"harthur": 3, "pull": 2},
                "outcome": [
                    ("n", "You get it out in one piece, standing up, not sitting, because sitting down would have made it a conversation."),
                    ("n", "He listens the whole way through without once making it easier for you, which you will later understand was the respect."),
                    ("Harthur", "You bought a stranger's life and spent it on mine."),
                    ("you", "Yes."),
                    ("n", "And he is quiet for a long moment, and when he speaks again there is something underneath it that was not there on the first night — something level and careful and a very long way from gratitude."),
                    ("Harthur", "Then I'm obliged to be worth it. I don't know how anybody would go about that, and I intend to find out, and I want you to understand that I will not be casual about it."),
                    ("!", "Nobody has ever said anything like that to you. You have been sworn to an institution since you were seventeen and not one living creature has ever once said that it intended to be worth you."),
                ],
                "next": "s_molt",
            },
            {
                "label": "Go home. Go to bed.",
                "detail": "It is done. It cannot be undone at this hour or any other.",
                "effects": {"change": 2},
                "outcome": [
                    ("n", "You sleep beautifully. Nine hours, no dreams, and you wake clear-headed and rested and hungry."),
                    ("!", "That is the part that will frighten you later."),
                ],
                "next": "s_molt",
            },
        ],
    },

    # ---------------------------------------------------------------- III
    "s_molt": {
        "act": "Night Three",
        "title": "The Seam",
        "journal": ["draught", "seam", "nail_school"],
        "text": [
            ("n", "You wake before the bell in a wet bed."),
            ("n", "Your first thought is the ordinary humiliating one and it lasts about a second and a half, which is how long it takes to get your hand round to your back and bring it out in front of your face in the grey light."),
            ("n", "It is not sweat. It is dark and thin and slightly thick between the fingers, and it smells, unmistakably, of almonds."),
            ("n", "You make an inventory because inventories are safer than conclusions: the hour, the wet sheet, the smell, the line of something raised beneath your shirt. You leave out the feeling that came with waking — not pain, exactly, but the shameful relief of finding an explanation, any explanation, for the pressure you have carried all week."),
            ("n", "Something along your spine has opened in the night and closed again before you woke. You can find the line of it, third vertebra to the small of the back, beneath a dry ridge that has marked the sheet with a neatness almost like handwriting."),
            ("n", "Under the ridge are plates. Smooth, warm, faintly ridged; when you breathe in, they move in sequence from the top down. You hold your breath to see whether they will stop. They do. You breathe again, and they begin before you do."),
            ("!", "You cannot see it. It is on your back. There is no mirror in this flat that will show you, and there is exactly one person in this city you could ask to look."),
            ("n", "You sit on the edge of the bed for some time holding a handful of your own bedsheet. Then, alone in a locked room in a city that hears everything, you say his name out loud, to test something."),
            ("!", "Harthur."),
            ("n", "The r comes out with a buzz underneath it. A second voice, half a tone down, arrives a fraction late. It is not quite an echo; it sounds more like a witness waiting for you to finish before correcting your account."),
            ("n", "The voice goes first. Nobody ever told you that, and yet you know it, the way you know to pull your hand out of a fire."),
            ("n", "You begin making the case for both explanations. The Draught, taken weekly since you were seventeen; Schedule Nine, page two, sixty-one entries. You arrange the facts so each side can acquit you, then notice you have not asked what you are trying to be acquitted of."),
            ("!", "Either there is a thing on Ashmoor Row and it is happening to you as well — or the Draught has finally done to you what the Draught does, and there is nothing on Ashmoor Row at all, and there never was."),
        ],
        "choices": [
            {
                "label": "Report to the Ordinance infirmary.",
                "detail": "Get it written down by somebody else. A record is a record.",
                "effects": {"suspicion": 3, "change": 1, "proof": 1},
                "flags": ["logged_body"],
                "outcome": [
                    ("n", "The physician runs his thumb the length of the seam twice, unhurried, the way you would test the ripeness of something."),
                    ("Physician", "Nothing at all. You're in excellent health. Genuinely — I'd be pleased with these numbers in a man of twenty."),
                    ("n", "Then he writes for a very long time. Four sides. He is still writing when you leave."),
                    ("!", "Nothing at all, and four sides of it. Whatever is on those four sides exists, and is in a building, and has a reference number, and is not inside your head. That is not nothing. That is the first thing in eight days that is not inside your head."),
                    ("n", "In the corridor a clerk you have never met greets you by name and asks, warmly, after your mother, who has been dead for twenty years and whom you have never once mentioned inside this building."),
                ],
                "next": "s_confession",
            },
            {
                "label": "Go to Ashmoor Row. Ask him to look at your back.",
                "detail": "He is the only person in Vantage who has never once been surprised by you.",
                "effects": {"harthur": 3, "pull": 3},
                "outcome": [
                    ("n", "You take your shirt off in his front room at the seventh quiet hour with the rain coming down the skylight, and you turn around, and you wait, which is the most frightened you have been in eleven years of professional fear."),
                    ("n", "He is quiet for so long that you start to turn back. His hand arrives flat between your shoulder blades and holds you exactly where you are."),
                    ("Harthur", "Don't. Give me a moment. I'm not shocked, I'm —"),
                    ("n", "He does not finish it. What he does instead is put his thumb to the seam and open it, about two inches, carefully, the way you would lift the corner of a dressing, and the sound that makes is small and wet and entirely new to you."),
                    ("n", "It does not hurt. It is the opposite of hurting. It is the precise relief of taking off a boot at the end of a long day and it goes the whole length of your spine, and you make a noise you have never made in front of another person."),
                    ("Harthur", "Oh, love."),
                    ("n", "He has never called you anything before. Not your name, not sir, not once in three nights, and you understand — standing there half-dressed and coming apart in a stranger's front room — that he has been carefully not doing it."),
                    ("Harthur", "Sit down. I'm going to put the kettle on, and then I am going to tell you a thing I should have told you on the first night, and I would like us both to be sitting when I do."),
                ],
                "next": "s_confession",
            },
            {
                "label": "Cut it out yourself. Keep what comes away.",
                "detail": "Nine inches of Ordinance iron, and a jar. Bring back something they can hold.",
                "effects": {"change": 2, "proof": 3},
                "flags": ["specimen"],
                "outcome": [
                    ("n", "You get the mirror off the wall and set it on a chair and work over your shoulder, backwards, by lamplight, which is a way of doing surgery that nobody has ever recommended."),
                    ("n", "The nail goes in easily. That is the worst part. It goes in the way a key goes into its own lock."),
                    ("n", "There is no pain. There is a sensation of being correctly assembled. You get your fingers in past the second knuckle and take hold of something warm and ridged and yours that does not want to come, and you brace your foot against the bedframe, and you pull until it does."),
                    ("n", "It is about the size of a thumb. Pale, segmented, jointed in three places. It flexes twice in the dish and then stops."),
                    ("!", "It is in a jar on your windowsill. It is still there in the morning. It is still there the morning after that, and it has not rotted, and it does not float."),
                    ("n", "By the third day the seam has closed over the cut and is a half-inch longer than it was."),
                ],
                "next": "s_confession",
            },
        ],
    },

    # ----------------------------------------------------------------- IV
    "s_confession": {
        "act": "Night Four",
        "title": "The Almond Room",
        "journal": ["the_face", "amendment", "maro", "calder_yard"],
        "text": [
            ("n", "Two cups are poured when you arrive. One of them is cold. He has been pouring the second one every night since the first, on the chance."),
            ("Harthur", "Sit on that side. Not because you'll want to run — because you'll want to not run, and I'd rather not make that harder than it already is."),
            ("n", "Then he puts both hands flat on the table."),
            ("n", "You will think about that afterward, the hands on the table, because it means that he knew exactly how much of it there was going to be."),
            ("n", "It starts at the jaw. The skin does not tear and it does not split; it parts, the way a thing being born parts what is in front of it, and it goes in one long unhurried movement from the hinge of the jaw down the throat and out across both shoulders, and there is a very great deal of fluid."),
            ("n", "It comes across the table. It is warm. It gets on your hands and down the front of your coat and one line of it goes across your mouth, and it tastes of almonds and iron and something underneath that is not on any list you were ever given."),
            ("n", "He comes out of the man the way an arm comes out of a sleeve turned inside out, and the man goes down over the back of the chair in a wet heap of itself and lies there, and it is the worst thing you have ever seen, and you have been to Marrow Street."),
            ("n", "What is left standing is tall. Not tall the way a man is tall — tall the way a room is tall, by having more places to be. Chitin the colour of old varnish. Too many joints, and every one of them gentle, folded in, tucked away, taking up as little of your evening as it can possibly manage."),
            ("n", "And low in the long dark plate of its back, sunk in, grown over, the flesh heaped up around it in a black wet lip that has been trying to close for twenty years and cannot close because there is iron in the way:"),
            ("!", "A nail. Nine inches. Ordinance issue. The crown worn smooth, and the whole of it weeping steadily down into the small of his back, and the stain of that going down the backs of both legs, old and layered and going nowhere."),
            ("n", "You ask who did it. Your voice does the thing that it now does. He answers as though you had asked him the time."),
            ("Harthur", "No idea. A nail, on a stair, in Calder Yard, a very long time ago. He'd have been about your age, at a guess. The building's a laundry now — I walk past it on Thursdays."),
            ("Harthur", "I'd like to be able to tell you it meant something. Everybody asks. There's nothing at the bottom of it. Somebody was issued iron and I was on the wrong landing."),
            ("Harthur", "I can't reach it. That's the joke, if you want one — it's four inches past anywhere I can go. And it won't close around it and it won't push it out, so it just goes on, and every year the face costs a little more, and I get about eleven hours of it now before I have to come home and be this in the dark."),
            ("n", "He tells you the rest with his back to you, working a scraper over a green civil volume out of pure habit, because he cannot keep still while he says it."),
            ("Harthur", "I take names out. Out of the Registry, out of the civil record, out of the books they send me to mend. Four hundred and six, since before you were sworn in. Children under their mothers first, then the old ones, then whoever I can reach."),
            ("n", "And you think of Warden Ilsabet Crow, promoted four times on a monster count that has fallen in every year of her career; of the Ordinance congratulating itself each spring on a victory delivered by one thin man with a scraper, working nights, in a room with wax in the grille."),
            ("n", "So you tell him about your mother."),
            ("n", "It comes out badly and in the wrong order — the stair, the sound like a cough, a hand across your eyes, the coat they let you keep. Ashmoor Row, third floor, the twelfth of a cold March."),
            ("!", "Maro."),
            ("n", "He puts the scraper down. He goes to the shelf. It takes him some time, and you work out somewhere in the middle of it what is about to happen, and you let it happen anyway."),
            ("n", "He comes back with a green civil volume, and opens it, and turns it around."),
            ("n", "She is in it. Unstruck. Whole. Her name and her trade and her address and the disposition code beside them in four-hundred-year-old ink, perfectly legible, waiting."),
            ("Harthur", "It's three shelves along. It has been three shelves along the entire time you have been in this room."),
            ("Harthur", "I never got to it. The Registry sends me what's damaged, in the order it gets damaged, and that volume has never once been damaged. It's had a good life on a dry shelf."),
            ("n", "There is no cruelty in this. There is no design in it either, and that turns out to be very much worse. Four hundred and six people are walking around Vantage tonight because a cart brought the right books on the right morning, and your mother is twenty years dead two streets from here because it did not."),
            ("Harthur", "I'm sorry. I would have. If anybody had ever told me."),
            ("n", "And then, because he has apparently decided that tonight is the night for all of it:"),
            ("Harthur", "I have been very careful with you. I want you to understand that it has been an effort."),
            ("Harthur", "Four nights. I have counted them. I count the hours in between, which is worse, and I know that it is worse. You keep coming back up those stairs and I have not once asked you to, and I have thought about asking you to, and I have decided against it eleven separate times, and I would like some credit for that."),
            ("Harthur", "If you go down tonight and you don't come back, I will know where you sleep. I have known since the second night. I'm telling you because you are the only creature in this city I have ever wanted to be honest with, and because I would rather you were frightened of me accurately than inaccurately."),
            ("n", "And the appalling thing — the thing you will not put in any report, the thing you will not say to Rell in the yard by the broken grille — is that you are not frightened."),
            ("n", "You are standing in a warm room with another creature's blood drying on your mouth, being told by something with nine joints in each arm that it knows where you sleep."),
            ("!", "And what you feel, precisely and unmistakably, is that you have been bored for eleven years."),
        ],
        "choices": [
            {
                "label": "\"Let me pull it out.\"",
                "detail": "Twenty years. It has to come out of someone, and you have hands.",
                "effects": {"harthur": 4, "pull": 3, "change": 1, "proof": 2},
                "flags": ["pulled_nail"],
                "outcome": [
                    ("n", "It cannot be done gently and you do not insult him by trying. You get both hands on the crown and your foot braced against the press, and it comes out of him in one long grinding pull with a sound like a nail leaving old oak, because that is precisely what it is."),
                    ("n", "What comes with it is twenty years of everything that could not get out past it. It goes across the floorboards and over your boots and keeps coming for a long moment after you would have said there was nothing left, and the smell in that room is a thing you will be able to summon at will for the rest of your life."),
                    ("n", "He makes no noise at all. He has had twenty years to practise making no noise."),
                    ("n", "Afterwards he is shaking and much smaller, and you are holding nine inches of Ordinance iron that has been inside a body since before you could read. He puts what is presently his forehead against your collarbone and stays there, and the rain goes on down the skylight, and neither of you says anything for a quarter of an hour."),
                    ("Harthur", "I'd forgotten. I had actually forgotten what the other thing feels like. Not-hurting. I thought I had made it up."),
                    ("!", "The nail is in your coat. It is iron, and it is real, and it is twenty years rusted, and no amount of anything can make it into a thing you imagined."),
                ],
                "next": "s_weight",
            },
            {
                "label": "Wipe your face. Keep the cloth.",
                "detail": "It is on you. It is outside your head. Get it into a jar before it dries.",
                "effects": {"harthur": -4, "proof": 4},
                "flags": ["cloth", "sampled"],
                "outcome": [
                    ("n", "You take the handkerchief out while he is still coming apart, and you wipe your mouth, and you fold it in on itself, and you put it away."),
                    ("n", "Then — because half measures are for people who have not been trained — you go along the table edge with it as well, and get the run off the boards, and squeeze it out into the empty cup."),
                    ("n", "He watches you do the whole of it. He does not stop you. At no point does he stop you."),
                    ("Harthur", "You'll want it kept cold. It goes off — four hours, perhaps five, and then it's only a stain, and a stain is nothing. They'll tell you it's glue."),
                    ("n", "He says it helpfully. He is being helpful. That is the part that gets in under your ribs and stays there: that his first instinct, standing in the wreck of his own face while you collect him into a teacup, is to make sure you get a usable sample."),
                    ("Harthur", "There. Now you've something for the file, and I've been of use, and we both know exactly what this was."),
                    ("!", "And the door goes quietly to, three rooms back, and the thing across the table is perfectly pleasant and has gone a very long way away."),
                ],
                "next": "s_weight",
            },
            {
                "label": "Step back. Put your hand on your own nail.",
                "detail": "Eleven years of training arrives all at once, and it arrives in your wrist.",
                "effects": {"harthur": -5, "pull": -3},
                "flags": ["drew_iron"],
                "outcome": [
                    ("n", "You are three steps back with the iron out before you have decided anything, which is what training is for and why they start it at seventeen."),
                    ("n", "The room does not move. The folded joints stay folded. It could cross that distance faster than you could turn your head and it does not, and the not-doing goes on and on until it becomes the loudest thing you have ever stood inside."),
                    ("Harthur", "That's all right."),
                    ("Harthur", "Take your time. I've got until dawn, and then I have to put the face on again, and I would honestly rather you did it before I go through all that twice in one night."),
                ],
                "next": "s_weight",
            },
        ],
    },

    # ------------------------------------------------------------------ V
    "s_weight": {
        "act": "Night Five",
        "title": "What He Wants",
        "journal": ["thirst", "amendment"],
        "text": [
            ("n", "You go back. Of course you go back. You have stopped constructing reasons; the reasons were embarrassing by the fourth night and by the fifth they are simply not there, and you climb four flights at the second quiet hour with nothing in your hands and nothing to say."),
            ("n", "He does not put the face on for you any more. He stopped asking whether that was all right, which is its own kind of answer, and the room is dark when you come in because the dark is easier on him and you have never once asked him to light it."),
            ("n", "You sit on the floor with your back against the press. Something long and jointed arranges itself along the boards beside you, carefully, leaving four inches of air — the way a dog that has been shouted at once will lie near you but not against you."),
            ("n", "After a while the four inches are not there any more. Neither of you mentions it."),
            ("Harthur", "I want to ask you for something, and I have been rehearsing it for two days, which you'll be able to tell, because it's going to come out like a document."),
            ("Harthur", "Stop taking the thimble."),
            ("n", "You say the obvious thing: that refusal is a disposition, that they count them, that Sollers would have it in the satchel inside a week."),
            ("Harthur", "Yes. I know. I've read the schedules — I bind them."),
            ("Harthur", "It's killing you. Twenty-nine, thirty, thirty-one. You've seen the column; you know the arithmetic better than I do. That is the honest reason and it is the whole of the reason I am allowed to give you."),
            ("n", "And then, after a silence that goes on slightly too long:"),
            ("Harthur", "It isn't the whole of the reason."),
            ("Harthur", "Without it you'll stop being able to see me. Not the man — the man is easy, anybody can see the man. Rell saw the man. Me. The lamp-sight is the only reason there is one creature in Vantage who has ever actually looked at me, and if you stop the thimble then that goes, and I have thought about it every hour for two days, and I want you to stop anyway."),
            ("Harthur", "I would rather be alone in a room with somebody who is alive than looked at by somebody who is being used up doing it."),
            ("n", "He is not touching you. He has been very careful not to be touching you for the entire length of that speech, and the carefulness is coming off him like heat off a stove."),
            ("!", "Eleven years in the Ordinance, and nobody in the whole of it has ever wanted a thing from you that cost them anything to want."),
        ],
        "choices": [
            {
                "label": "Stay. Let the thimble go.",
                "detail": "Do not go down the stairs tonight. Do not go down them on Thursday either.",
                "effects": {"harthur": 5, "pull": 5, "change": 2, "suspicion": 1},
                "flags": ["stayed", "off_draught"],
                "outcome": [
                    ("n", "You do not go down the stairs."),
                    ("n", "The four inches of air are gone for good somewhere around the fourth hour, and you find, in the dark, with both hands, that the folded gentleness of him is warm the whole way through, and that the joints move if you ask them to, and that the sound he makes when you find the hollow at the back of the plate is not a sound a man could make."),
                    ("n", "He shakes for most of it. Not fear. He tells you, a long time later, with his face somewhere in your neck and his voice doing something complicated, that nothing has touched him on purpose since the Calder Yard stair, and that he had made his peace with that, and that he would like it on the record that he had genuinely made his peace with it."),
                    ("n", "In the morning there is blood on the sheets in a quantity that would end most people's week."),
                    ("!", "You check yourself over twice and you are not cut anywhere. You look at him, and he says, quite honestly, that he does not think it is his either."),
                    ("n", "You throw the thimble out on the Tuesday. By the Friday your hands have started doing a thing when you are not watching them, and you do not tell him, and you are not entirely sure why you do not tell him."),
                ],
                "next": "s_taken",
            },
            {
                "label": "\"Strike her out first. Tonight. I'll hold the lamp.\"",
                "detail": "Twenty years late. Do it anyway. Do it while I watch.",
                "effects": {"harthur": 2, "pull": 2, "proof": 1},
                "flags": ["maro_struck"],
                "outcome": [
                    ("n", "He looks at you for a moment and then he does not argue, and you will be grateful for that later, because an argument would have been kind and you had not come here for kind."),
                    ("n", "It takes about forty minutes. He works the way a man works on something that matters and cannot be gone back over, and you hold the lamp, and it burns through your eyes the entire time, and you do not put it down."),
                    ("n", "It changes nothing. She has been dead for twenty years and a scraped page does not reach backwards."),
                    ("!", "You watch the last of her go down into the grain, and you find that it matters enormously, and you could not explain why to a board of inquiry, and you have no intention of ever trying."),
                    ("Harthur", "There. Nobody can prove she was ever here."),
                    ("Harthur", "It's the only funeral I know how to conduct. Four hundred and seven of them now, and I have never once managed to say anything at any of them."),
                    ("n", "He gives you the scrapings folded into a paper. A thimbleful of grey dust that used to be a woman's name. You put it in your breast pocket, and it is still there at the end of everything."),
                ],
                "next": "s_taken",
            },
            {
                "label": "Go home. Take the thimble. Write the report.",
                "detail": "You are an officer of the Ordinance and this has gone far enough.",
                "effects": {"harthur": -4, "pull": -4, "suspicion": -2, "proof": 1, "change": -1},
                "flags": ["went_home"],
                "outcome": [
                    ("n", "You get up off the floor. It takes a while. He does not help and he does not hinder and he does not say one single word, which is the cruellest thing available to him and which you are fairly sure he does not know he is doing."),
                    ("n", "You take the thimble at the door of your own flat, standing up, not sitting, and it goes down like a mouthful of pennies."),
                    ("n", "Then you write it. Four hours, eleven pages, everything — the finger, the jaw, the nail in the back, the four hundred and six, the eleven feet of roof gap, the seam in your own spine. It is the most thorough document you have produced in your life, and it is entirely accurate, and you know before you have finished it that you will never hand it in."),
                    ("!", "It goes under the floorboard. It is still eleven pages in the morning. Whatever else is or is not happening in this city, you have written eleven pages, and they are paper, and you can hold them."),
                ],
                "next": "s_taken",
            },
        ],
    },

    # ----------------------------------------------------------------- VI
    "s_taken": {
        "act": "Night Six",
        "title": "Quiet Hours",
        "journal": ["mire", "tallow_yard", "quiet_room"],
        "text": [
            ("n", "They come for the building at the third quiet hour."),
            ("n", "Not quietly — that is a thing people get wrong about the Ordinance. It comes up a stairwell like a household moving furniture, in no hurry, with a list."),
            ("n", "There is a crowd in the street by the time you get to a window. Not a mob; nothing so dramatic. Neighbours, in coats over nightclothes, standing well back on the far pavement in the attitude of people at a shop window. Somebody has carried a chair out for an older woman. Two doors along, a man is chalking his own door, in front of everybody, to be clear about where he stands."),
            ("n", "From the landing above you watch them take Rell Oduya out of Flat Eleven in his nightshirt with his lamp still on the table."),
            ("n", "He talked in his sleep. That is the whole of it. Eleven years of service and a clean file and a habit of saying things at four in the morning to nobody."),
            ("n", "He sees you on the stair. He stops, between two wardens, and his face does something you will never afterwards be able to describe to anyone, because it is pride."),
            ("Rell", "It was my wife who reported me. Good girl. Straight down the office with it, first thing."),
            ("n", "Then they take him down and the wagon does not leave."),
            ("!", "The wagon does not leave, because the list is not finished."),
            ("n", "Behind you, in the dark of Flat Six, Harthur is putting the face on three hours early. It takes eleven minutes now, and it is not a thing that can be watched politely; there is a great deal of it and most of it ends up on the floor. He does it anyway, because if they come through that door he would rather look like something they might merely arrest."),
            ("n", "He is still pushing the jaw into place when he starts talking."),
            ("Harthur", "There's a way into the Mire from the coal cellar. There's a scraper and a lamp in my coat. And there's the door, and you've a badge and a clean file, and I'd think less of nobody."),
            ("Harthur", "Choose fast. I'm not able to want anything at the moment, so it will have to be you."),
            ("n", "Which is a lie, and both of you know that it is a lie, and he tells it anyway, as the last courtesy he has left to give you."),
        ],
        "choices": [
            {
                "label": "Open the door.",
                "detail": "You have a badge, a nail, and a clean file. There is still a version of this you survive.",
                "effects": {},
                "next": resolve_door,
            },
            {
                "label": "Take the coal cellar. Go down into the Mire.",
                "detail": "Under Vantage there is black water and no ledger at all.",
                "effects": {},
                "next": resolve_run,
            },
            {
                "label": "Go to Tallow Yard and burn the Registry.",
                "detail": "Ninety thousand names in one long room, and you know the night clerk.",
                "effects": {},
                "next": resolve_burn,
            },
        ],
    },

    # ------------------------------------------------------------ ENDINGS
    "e_amended": {
        "kind": "ending",
        "act": "Ending",
        "title": "The Amended Name",
        "color": "#d9a441",
        "text": [
            ("n", "You go down through the coal cellar into water that is warm, which is the first thing nobody ever tells you about the Mire."),
            ("n", "He carries the ledger. Of course he carries the ledger; he has carried it for twenty years and it would not occur to him to leave it for the fire."),
            ("n", "Under the Cattle Gate, by lamplight, on a shelf of dry brick above the black water, he does the last amendment of his career. Two lines. His own, which was never really his. And yours, which takes him a great deal longer, because you have to sit there and watch a man scrape away the only proof you were ever born, and because he keeps stopping to ask whether you are sure."),
            ("n", "Four hundred and seven times he has done this for people who never learned his name. You are the only one who has ever been in the room."),
            ("Harthur", "There. You're nobody."),
            ("Harthur", "I'm sorry. It's the only safety I know how to make, and it's a poor one, and it's the whole of what I have."),
            ("n", "You come up at the river at the sixth quiet hour with the fog going gold at the edges."),
            ("n", "He holds the face the whole way to the water, and it costs him, and you can see precisely what it costs — the jaw is not sitting right, and there is something wrong with the left hand that he keeps in his pocket — and about a hundred yards short of the bank you tell him to stop."),
            ("n", "He looks at you. The fog is thick. There is nobody on the towpath at this hour and no grille within half a mile, and the whole grey world is, for one morning, not listening."),
            ("n", "So he stops."),
            ("n", "It is not quick and it is not quiet and it goes all over the towpath, and you stand in it and hold on to what is left when it is done, and it holds on back with rather more arms than the situation strictly requires."),
            ("Harthur", "You could have let me keep it on for the boat."),
            ("you", "No."),
            ("Harthur", "No. All right. No."),
            ("!", "Somewhere behind you the Ordinance is looking for two people who, on paper, were never born."),
            ("n", "It is very good at looking. It has absolutely no idea what it is looking for."),
        ],
    },

    "e_mire": {
        "kind": "ending",
        "act": "Ending",
        "title": "Two Bodies, One Ledger",
        "color": "#4f7d5c",
        "text": [
            ("n", "You do not make the river. You do not, in the end, particularly try."),
            ("n", "It takes eleven days to stop putting the face on, and they are the worst eleven days of your life, and he does not leave the water once in the whole of them."),
            ("n", "On the fourth day the voice goes entirely. You keep forming words in your mind, as if the right sentence could call it back. On the seventh the seam opens the rest of the way down and does not close. For an hour your body follows a logic you cannot translate, while you keep trying to decide whether the fear belongs to you or to the part of you that is leaving."),
            ("n", "He holds your head out of the black water for most of it. He does not tell you that it will be all right; he has never lied to you and he is not going to take it up at the end. What he says, over and over, in a voice that is by then not using a mouth, is that he is here, and that he is not going anywhere, and that he has got you."),
            ("n", "On the eleventh day you stop trying to negotiate with it. You let go and go down into the older, patient shape. The relief is so total that you cannot tell whether you have been rescued or have simply stopped being able to object."),
            ("n", "There are more of you down here than the Ordinance would survive knowing. Four hundred and seven names came off the books over two decades, and a fair number of them came down these stairs and simply went on existing, out of spite and warm water."),
            ("n", "You are not a person any more, in the sense that the ledger means person. You are not certain you ever met the standard."),
            ("!", "What you are is with him, which turns out to have been the load-bearing part."),
            ("n", "He has stopped leaving four inches of air. It took him until the second winter. You have never once mentioned it, because you understand exactly what it cost him, and because there are some things you do not say out loud even where there is nothing left to listen."),
        ],
    },

    "e_struck": {
        "kind": "ending",
        "act": "Ending",
        "title": "Both Names Struck",
        "color": "#d9542b",
        "text": [
            ("n", "The Registry is four hundred years of other people's names in one long room on Tallow Yard, and it goes up like a thing that has been waiting."),
            ("n", "He does the shelves at the north end. You do the south. He works faster than you because he has more arms available and has stopped pretending otherwise, and at some point in the middle of it, in the smoke, you catch yourself laughing, which is not a thing you have done since you were six."),
            ("n", "You are not brave. You want to be extremely clear with yourself about this at the end. You are simply out of other doors, and there is a difference, and it has never mattered less."),
            ("n", "Tallow Yard seals automatically in the event of fire. Standard procedure. Schedule 2, four lines below the clause about the duplicates, and you have read them both, and you came anyway, and so did he, and neither of you said a word about it on the walk over."),
            ("n", "He gets a hand around yours in the last of it. Too many joints. Perfectly steady."),
            ("Harthur", "Did we get the M's?"),
            ("you", "We got the M's."),
            ("Harthur", "Good. Good. Everybody at once, then. I have wanted to do it that way for twenty years and I could never work out how."),
            ("n", "In the morning there is no Registry. There is no flag on Flat Six, no disposition on Mrs. Anselm, no woman called Maro sitting three shelves along in perfect condition waiting for a repair that was never going to be ordered, and no ninety thousand names."),
            ("n", "There is a city full of people the Ordinance cannot prove."),
            ("n", "It will start a new book. Of course it will start a new book. But somebody will have to bind it —"),
            ("!", "— and the best binder in Vantage is a double handful of warm ash on a stair that will smell, faintly, for years afterward, of almonds."),
        ],
    },

    "e_clean_report": {
        "kind": "ending",
        "act": "Ending",
        "title": "A Clean Report",
        "color": "#6f7580",
        "text": [
            ("n", "You go down as far as the coal cellar with him and you stop on the third step, and he gets to the bottom before he notices, and then he stands in the dark with the lamp held up, waiting, for a length of time that you will be paying interest on for the rest of your life."),
            ("Harthur", "Ah."),
            ("Harthur", "No — quite right. Quite right. You've a file and a pension, and I am, when you take the whole of it into account, an enormous amount of trouble."),
            ("n", "He goes. He does not look back, which is a kindness, and you understand it as a kindness, which is somehow the worst available outcome."),
            ("n", "Upstairs you are extremely helpful. You know nothing, you saw nothing, your file is exemplary and Warden Crow says so in writing. They give you Rell's district. You are good at it."),
            ("n", "The seam on your back stops at the fourth vertebra and goes no further. It opens perhaps twice a year, always in the small hours, always in a bed you are alone in, and you have the business of the sheets down to a routine now — cold water first, and never send them out."),
            ("n", "You buy a mirror, which is permitted and in fact quietly encouraged. You hang it in the hall. After a week you turn it to the wall, which is not forbidden, because it has not yet occurred to anybody to forbid it."),
            ("!", "You live. That was the thing you chose, and you got it, and it was never once in question after the third step."),
            ("n", "Some nights on the Ashmoor beat there is almonds on a stairwell and you stand in it until it goes. It takes about four minutes. You have timed it, more than once, which tells you everything you need to know about how the rest of this is going to go."),
        ],
    },

    "e_quiet_room": {
        "kind": "ending",
        "act": "Ending",
        "title": "The Quiet Room",
        "color": "#8e1f3d",
        "text": [
            ("n", "Nobody hurts you. You should understand that at the outset, because it is the entire method and it took the Ordinance four hundred years to arrive at."),
            ("n", "The Quiet Room is white and warm and has a drain in the floor and a chair that is genuinely comfortable. Warden Crow brings you tea, which is not as good as his."),
            ("n", "They bring him in unheld. They will not let him put the face on — they have been very thorough about that, and the floor of the corridor outside shows how thorough, and the two men with the hoses are already waiting at the end of it as a matter of routine."),
            ("n", "He is folded down as small as a thing that size can fold, in a white room, under a light that leaves him nowhere, with the hole in his back weeping steadily onto the tiles where the iron came out."),
            ("Crow", "Look at it and tell me what it is. That's all. Then you can go home."),
            ("n", "You look at it for a long time. You look at the folded gentleness of it, every joint tucked in. You think about four inches of air on a dark floor, and how long it took him to give them up, and the thing he said about being frightened of him accurately."),
            ("n", "And you find, when you go looking for it, that your mouth is very willing."),
            ("you", "That's a monster."),
            ("n", "It does not argue. It has never once argued about anything."),
            ("n", "They give you a commendation, a new district, and a flat with a window. You keep the flat very clean."),
            ("n", "Once a year, on an anniversary you were never told about and cannot name, you smell almonds on a stair and a small grief arrives with no paperwork attached to it, and you file it correctly, and it goes away."),
            ("n", "You are forty next spring. No hunter has ever been forty. You do not wonder about this."),
            ("!", "You love the Ordinance. You have always loved the Ordinance."),
        ],
    },

    "e_mercy": {
        "kind": "ending",
        "act": "Ending",
        "title": "The Hunter's Mercy",
        "color": "#9a6b4f",
        "text": [
            ("n", "You do it yourself. On the landing, before they are up the second flight, with your own iron, because you have seen the Quiet Room's intake ledger and you know to the hour how long they keep a thing alive in there."),
            ("n", "This is the argument you will use. It is a good argument. It happens to be true."),
            ("n", "It takes him a long time to die and he spends nearly all of it holding still, so that you do not have to work hard. Twice he moves a limb out of your way. The second time you understand that he is helping, and you keep going, because stopping would have made it worse for him, and because you are not certain you could have started again."),
            ("Harthur", "It's all right. Four nights. That's four more than I had budgeted for."),
            ("n", "He says it twice and then he cannot say anything, and the shape goes out of him by degrees, from the outside in, the joints letting go one at a time like a house being closed up for the winter."),
            ("n", "The stairwell has to be hosed. They send two men and it takes them most of the morning, and one of them complains about the smell, and you stand at the top of the flight and listen to a stranger complain about the smell."),
            ("Crow", "Twenty years we've been missing that. And done by a Third Nail on his own initiative. I'll see it's said properly, in writing."),
            ("n", "They promote you. They give you the Ashmoor beat, which they intend as an honour."),
            ("n", "Three months later, washing, you find a hardness under the skin at the base of your spine. Iron. You know the length of it without measuring, because you have carried the standard issue since you were seventeen."),
            ("!", "It is working its way in, rather than out."),
            ("n", "You do not have it removed. You tell yourself that it cannot be reached."),
            ("n", "This is true. It is not the reason."),
        ],
    },

    "e_verminous": {
        "kind": "ending",
        "act": "Ending",
        "title": "Verminous",
        "color": "#6c6552",
        "text": [
            ("n", "You do not get three streets."),
            ("n", "It is not the wardens. It is the stairs, and then the wall beside the stairs, and then the discovery — sudden, total, delivered by your own body without consultation — that the wall is easier."),
            ("n", "The thought arrives already defended: the wall is nearer, the ceiling is quiet, the floor has asked too much of you. You know these are symptoms. You also know how convincingly a person can reason toward the thing they have already begun to do."),
            ("n", "They find you on the ceiling of the second landing and they are very calm about it, because there is a procedure, and the procedure is old, and it was written by people who knew exactly how hunters end."),
            ("doc", "DISPOSAL ORDER — INTERNAL\nSUBJECT: Third Nail, Ashmoor beat\nCAUSE: Draught, cumulative. Expected.\nMETHOD: hold to conclusion. Do not intervene.\nNOTE: allocate replacement from the Nail School intake.\nThey come up quickly."),
            ("n", "They put you in a cell with a drain and they do not touch you and they do not question you, because there is nothing you know that they have not known since before you were born, and it is not that kind of institution anyway. It is a tidy one."),
            ("n", "The voice is gone by the second day. On the third the seam finishes what it has been doing since Night Three, and most of what you were goes down the drain over about six hours, and on the fourth you stop trying to explain, which is a relief so large that it is almost a pleasure."),
            ("n", "In the morning the charwoman opens the cell to sweep and finds it dry and light in there, like a thing made of paper and legs, and she calls down the stair in a cheerful voice — it's finished, it's all finished, come and look — and they come, and they look, and they agree that the room feels bigger."),
            ("n", "Somebody says that it was a mercy. Somebody always does."),
            ("!", "Your name is in the book. It is in the book correctly, in full, in a clerk's excellent hand, with your intake year and your district and — as of this morning — a disposition."),
            ("n", "It says INTERNAL. It has said INTERNAL for everybody since 1911 and it will go on saying it, because the roll is a tidy document and the Ordinance is a tidy institution, and there has never been anything about any of this that was not written down in advance."),
            ("n", "Four streets away Harthur is sitting up with the face on and two cups poured, one of them going cold."),
            ("n", "He will go on doing that for eleven more nights before he stops."),
        ],
    },

    "e_ash": {
        "kind": "ending",
        "act": "Ending",
        "title": "Ash and Nothing",
        "color": "#43444b",
        "journal": ["duplicates"],
        "text": [
            ("n", "You burn the wrong building."),
            ("n", "Not the wrong address. The wrong building."),
            ("n", "Every civil record in Vantage has been duplicated nightly to the sub-annex at Calder Yard since the fire of '09, a fact printed in the second schedule of the ordinances you swore an oath to enforce, and which you have never once read, because nobody reads them, because reading them is a disposition."),
            ("n", "By the second quiet hour the clerks are already copying it all back. They are cheerful about it. It is overtime."),
            ("n", "Crow does not even have you brought in. She comes to the yard herself and stands with you watching the roof go, hands behind her back, entirely without malice, which is the part you will not be able to get past."),
            ("Crow", "Four hundred years of paper. You know what's in that room? Copies. It's been copies since before my mother."),
            ("Crow", "The building isn't the record. The habit is the record. You can't burn a habit, dear. People keep doing it."),
            ("n", "They take you at dawn. They take him at noon, in the Ashmoor market, in daylight, without hurrying, and he does not run, because there is nowhere left in the ledger for him to run to."),
            ("n", "One thing survives, and he works it out in the cell before you do, and it is the only time in six nights that you ever hear him pleased."),
            ("Harthur", "The four hundred and six."),
            ("Harthur", "They copy what's on the page. They have always only ever copied what's on the page. Every name I took out was out before the copy was made — it has been going into the duplicate as a blank for twenty years, every night, in the Ordinance's own hand."),
            ("n", "Four hundred and six people go on walking around a city that has just rebuilt the whole of its memory from scratch and still cannot prove a single one of them."),
            ("n", "It is not nothing. It is a very long way from nothing."),
            ("n", "It is also, set against ninety thousand names and a building you burned down for no reason, extremely close to nothing indeed, and both of these are entirely true, and you are going to have a great deal of time in which to hold them both at once."),
            ("!", "On the new page — good paper, fresh binding, somebody else's hand — you are written directly under him, the way children are written under their mothers."),
            ("n", "Neither line has ever been struck out since."),
        ],
    },

    "e_nosuchman": {
        "kind": "ending",
        "act": "Ending",
        "title": "No Such Man",
        "color": "#5a5470",
        "journal": ["draught"],
        "text": [
            ("n", "The stair at Ashmoor Row smells of damp."),
            ("n", "Only damp. You stand on the fourth landing for a long time with your eyes shut, working at it, and it is damp, and old plaster, and somebody's cabbage from two floors down."),
            ("n", "Flat Six has been empty for eleven years."),
            ("n", "The landlord has the book out to show you before you have finished asking, because you have a badge and people show you things. Eleven years of void in a column ruled for rent. No binder. No tenant at all since a Mrs. Keel died in the back room in '27."),
            ("n", "The Registry has no flag numbered 44-118-C. The Registry has never had a flag numbered 44-118-C; the series runs 44-117 to 44-119 with no gap in it, and the clerk turns the page around so that you can see there is no gap, and is patient with you about it."),
            ("Rell", "Harthur."),
            ("Rell", "No. No, mate. Never heard it."),
            ("n", "He is kind about it. He is kind about it in the specific, careful way that frightens you, and he does not mention it again, and he is standing in the corridor with Sollers three days later when they come to take your lamp."),
            ("n", "Warden Crow does not make a thing of it. She has the physician's four sides in front of her, and the stairwell log with eleven separate entries on it — up at the second quiet hour, down at the sixth, over and over, into a building with nobody in it."),
            ("Crow", "Schedule nine. Page two. I did tell you, dear."),
            ("Crow", "Sixty-one entries, and number nine is the one that gets the good ones. Attachment to a figure not otherwise attested. It is always the lonely ones, and it is always the ones who are good at the work, and I have signed eleven of these in my career and I have never yet been able to make a single one of you believe it."),
            ("n", "They are not unkind. You want that written down somewhere. Nobody is ever unkind."),
            ("n", "There is a ward at Calder with high windows, and they take you off the Draught slowly, over four months, because taking a man off it quickly is how you lose him. The seam on your back closes in the third month and does not open again."),
            ("n", "By the spring you can hold the whole of it in your head at once without your heart going, and the physician calls that excellent progress, and writes it down."),
            ("n", "Here is what you have. No cloth, no jar, no nail, no ledger, no scrapings folded in a paper. Nothing came home in your pockets from any of those eleven nights, and you have turned the coat inside out, and you have been through the floorboard, and there is nothing under the floorboard."),
            ("!", "Everything you ever knew about him, you knew through a lamp that burns inside your own eyes. There was never one single thing that would survive being written down."),
            ("n", "So it was the Draught. Obviously it was the Draught. Four hundred and eleven hunters and not one of them makes it to thirty-three, and this is what that looks like from the inside, and you have the paperwork, and the paperwork is the only thing in this entire city that has ever been able to prove anything."),
            ("n", "You believe that. Most days you genuinely believe it."),
            ("n", "But some nights in the ward you wake before the bell with your back aching at the third vertebra, and there is a smell in the room that the high windows have not let in, and you lie in the dark and think about a man who would have had every reason in the world to make quite sure that nothing of him was ever left in your pockets."),
            ("!", "And that thought is warm. That is the trouble with it. Four months of excellent progress, and the thought that he was real, and careful with you to the very end, is still the warmest thing you own."),
        ],
    },
}


# ----------------------------------------------------------------------------
# RENDERING
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
      .stApp { background: #0f0e12; }
      .main .block-container { max-width: 760px; padding-top: 2.2rem; }
      .stApp:has(.qh-start-hero) {
          background:
              radial-gradient(ellipse at 50% 0%, rgba(91, 67, 54, .23), transparent 48%),
              linear-gradient(180deg, #171612 0%, #111114 46%, #0d0d10 100%);
      }
      .main .block-container:has(.qh-start-hero) {
          max-width: 900px;
          padding-top: 3.5rem;
          padding-bottom: 4rem;
      }
      .qh-start-hero {
          position: relative;
          padding: 1.25rem 0 2rem;
          margin-bottom: 1.25rem;
          border-bottom: 1px solid rgba(190, 157, 106, .28);
          animation: qh-arrive .9s ease-out both;
      }
      .qh-start-hero:after {
          content: "";
          display: block;
          width: 3.5rem;
          height: 2px;
          margin-top: 1.3rem;
          background: #a33f35;
          box-shadow: 0 0 18px rgba(163, 63, 53, .65);
      }
      .qh-start-kicker, .qh-paper-label {
          font-family: ui-monospace, "SF Mono", monospace;
          font-size: .68rem;
          letter-spacing: .2em;
          line-height: 1.5;
          text-transform: uppercase;
      }
      .qh-start-kicker { color: #b28d5c; margin-bottom: .8rem; }
      .qh-start-hero h1 {
          font-family: Georgia, "Iowan Old Style", serif;
          font-size: clamp(3.1rem, 5vw, 4.8rem);
          font-weight: 400;
          line-height: 1;
          color: #e8dfce;
          margin: 0;
      }
      .qh-start-subtitle {
          max-width: 38rem;
          margin: 1rem 0 0;
          color: #aaa297;
          font-family: Georgia, "Iowan Old Style", serif;
          font-size: 1.08rem;
          line-height: 1.65;
      }
      .qh-start-stamp {
          margin-top: 1.1rem;
          color: #a65549;
          font: .66rem/1.5 ui-monospace, "SF Mono", monospace;
          letter-spacing: .13em;
          text-transform: uppercase;
      }
      .qh-paper {
          position: relative;
          color: #332d23;
          background-color: #d6c7a7;
          background-image:
              repeating-linear-gradient(0deg, rgba(70, 53, 31, .035) 0, rgba(70, 53, 31, .035) 1px, transparent 1px, transparent 4px),
              radial-gradient(ellipse at 8% 12%, rgba(255, 247, 216, .55), transparent 48%),
              radial-gradient(ellipse at 93% 82%, rgba(96, 65, 34, .16), transparent 52%);
          border: 1px solid rgba(214, 192, 151, .55);
          box-shadow: 0 12px 34px rgba(0, 0, 0, .27), inset 0 0 28px rgba(94, 68, 39, .12);
          padding: 1.35rem 1.55rem;
          margin: 0 0 1.1rem;
          animation: qh-arrive .7s ease-out both;
      }
      .qh-paper:nth-of-type(2) { animation-delay: .08s; }
      .qh-paper:nth-of-type(3) { animation-delay: .16s; }
      .qh-paper:nth-of-type(4) { animation-delay: .24s; }
      .qh-paper-label { color: #795c39; margin: 0 0 .7rem; }
      .qh-paper p, .qh-paper .qh-brief p {
          color: #393329;
          font-family: Georgia, "Iowan Old Style", serif;
          font-size: .98rem;
          line-height: 1.72;
      }
      .qh-paper p:last-child { margin-bottom: 0; }
      .qh-paper b { color: #201d18; }
      .qh-paper table {
          display: block;
          width: 100%;
          overflow-x: auto;
          border-collapse: collapse;
          color: #393329;
          font: .78rem/1.55 Georgia, "Iowan Old Style", serif;
      }
      .qh-paper th, .qh-paper td {
          padding: .55rem .6rem;
          border-bottom: 1px solid rgba(90, 68, 40, .24);
          text-align: left;
          vertical-align: top;
      }
      .qh-paper th {
          color: #795c39;
          font: .62rem/1.4 ui-monospace, "SF Mono", monospace;
          letter-spacing: .08em;
          text-transform: uppercase;
      }
      .qh-opening-copy {
          color: #393329;
          font: .98rem/1.75 Georgia, "Iowan Old Style", serif;
          margin: 0 0 .85rem;
      }
      .qh-opening-doc {
          color: #574933;
          border-top: 1px solid rgba(90, 68, 40, .35);
          padding-top: .85rem;
          margin: 1rem 0 0;
          white-space: pre-wrap;
          font: .76rem/1.8 ui-monospace, "SF Mono", monospace;
      }
      .main .block-container:has(.qh-start-hero) .qh-brief-h { display: none; }
      .main .block-container:has(.qh-start-hero) .qh-rule { border-color: rgba(190, 157, 106, .28); }
      .main .block-container:has(.qh-start-hero) [data-testid="stCaption"] { color: #827d74; }
      .main .block-container:has(.qh-start-hero) .stTextInput label { color: #c4b9a5; }
      .main .block-container:has(.qh-start-hero) .stButton > button {
          border-color: #8d392f;
          background: #742e28;
          color: #f1e6d2;
      }
      .main .block-container:has(.qh-start-hero) .stButton > button:hover {
          border-color: #b05a47;
          background: #8b382e;
          color: #fff4df;
      }
      @keyframes qh-arrive {
          from { opacity: 0; transform: translateY(9px); }
          to { opacity: 1; transform: translateY(0); }
      }
      @media (prefers-reduced-motion: reduce) {
          .qh-start-hero, .qh-paper { animation: none; }
      }
      @media (max-width: 640px) {
          .main .block-container:has(.qh-start-hero) { padding-top: 2rem; }
          .qh-start-hero h1 { font-size: 3.1rem; }
          .qh-paper { padding: 1.1rem; }
      }
      .qh-act {
          font-family: ui-monospace, "SF Mono", monospace;
          letter-spacing: .28em; text-transform: uppercase;
          font-size: .72rem; color: #7c7486; margin-bottom: .2rem;
      }
      .qh-title {
          font-family: Georgia, "Iowan Old Style", serif;
          font-size: 2.1rem; color: #e8e2d9; margin: 0 0 1.4rem 0;
          font-weight: 400; letter-spacing: .01em;
      }
      .qh-n {
          font-family: Georgia, "Iowan Old Style", serif;
          font-size: 1.04rem; line-height: 1.78; color: #cec7bd;
          margin: 0 0 1.05rem 0;
      }
      .qh-beat {
          font-family: Georgia, serif; font-size: 1.1rem; line-height: 1.7;
          color: #e8dcc0; font-style: italic;
          border-left: 2px solid #8c6f3f; padding: .1rem 0 .1rem 1.1rem;
          margin: 1.4rem 0;
      }
      .qh-speaker {
          font-family: ui-monospace, "SF Mono", monospace; font-size: .7rem;
          letter-spacing: .2em; text-transform: uppercase;
          color: #9a8fa8; margin-bottom: .3rem;
      }
      .qh-line {
          background: #171620; border: 1px solid #272433; border-radius: 3px;
          padding: .85rem 1.1rem; margin: 0 0 1.05rem 0;
          display: flex; gap: .9rem; align-items: flex-start;
      }
      .qh-face {
          flex: 0 0 46px; width: 46px; height: 46px; border-radius: 2px;
          object-fit: cover; object-position: 50% 22%;
          border: 1px solid #272433;
          filter: grayscale(1) brightness(.62) contrast(1.15);
      }
      .qh-said { flex: 1 1 auto; min-width: 0; }
      .qh-line p {
          font-family: Georgia, serif; font-size: 1.05rem; line-height: 1.65;
          color: #ddd5ea; margin: 0;
      }
      .qh-doc {
          font-family: ui-monospace, "SF Mono", monospace; font-size: .78rem;
          line-height: 1.75; color: #9d9482; white-space: pre-wrap;
          background: #14130f; border: 1px dashed #3a3629;
          padding: .95rem 1.1rem; margin: 0 0 1.15rem 0;
      }
      .qh-end {
          border: 1px solid; border-radius: 4px;
          padding: 1.5rem 1.6rem; margin-bottom: 1.6rem;
      }
      .qh-end h2 {
          font-family: Georgia, serif; font-weight: 400;
          margin: .2rem 0 0 0; font-size: 1.9rem;
      }
      .qh-end .qh-act { margin: 0; }
      .qh-rule { border: 0; border-top: 1px solid #262330; margin: 1.8rem 0; }
      .qh-page {
          min-height: 260px;
          display: flex; flex-direction: column; justify-content: center;
      }
      .qh-page > *:last-child { margin-bottom: 0 !important; }
      .qh-pagemark {
          font-family: ui-monospace, "SF Mono", monospace;
          letter-spacing: .22em; font-size: .68rem; color: #5f5869;
          text-align: right; margin: 0 0 .1rem 0;
      }
      @media (max-width: 640px) {
          .qh-page { min-height: 190px; }
      }
      .qh-jnote {
          font-family: Georgia, serif; font-size: .96rem; line-height: 1.72;
          color: #c3b9ab; font-style: italic;
          border-left: 2px solid #4a3f2c; padding-left: .95rem;
          margin: .65rem 0 .15rem 0;
      }
      .qh-notebook-page {
          position: relative;
          min-height: 410px;
          padding: 1.55rem 1.25rem 2.8rem 2.8rem;
          margin: .7rem 0 1rem;
          color: #382f26;
          border: 1px solid #b7a987;
          background-color: #e4dac2;
          background-image:
              linear-gradient(90deg, transparent 0, transparent 2.75rem, rgba(151, 57, 46, .4) 2.78rem, rgba(151, 57, 46, .4) 2.83rem, transparent 2.86rem),
              repeating-linear-gradient(180deg, transparent 0, transparent 30px, rgba(80, 111, 122, .19) 31px, transparent 32px),
              radial-gradient(ellipse at 14% 8%, rgba(255, 251, 225, .62), transparent 56%),
              radial-gradient(ellipse at 92% 91%, rgba(96, 65, 34, .14), transparent 52%);
          box-shadow: 0 12px 34px rgba(0, 0, 0, .32), inset 0 0 30px rgba(94, 68, 39, .1);
      }
      .qh-notebook-left {
          border-right: 0;
          box-shadow: 0 12px 34px rgba(0, 0, 0, .32), inset -12px 0 18px -18px rgba(45, 35, 27, .8), inset 0 0 30px rgba(94, 68, 39, .1);
      }
      .qh-notebook-right {
          border-left: 1px solid #aa9b7d;
          box-shadow: 0 12px 34px rgba(0, 0, 0, .32), inset 12px 0 18px -18px rgba(45, 35, 27, .8), inset 0 0 30px rgba(94, 68, 39, .1);
      }
      .qh-notebook-kicker {
          color: #805239;
          font: .64rem/1.5 ui-monospace, "SF Mono", monospace;
          letter-spacing: .17em;
          text-transform: uppercase;
          margin-bottom: .35rem;
      }
      .qh-notebook-page h2 {
          color: #302820;
          font: 400 1.8rem/1.2 Georgia, "Iowan Old Style", serif;
          margin: 0 0 1.1rem;
      }
      .qh-notebook-official {
          color: #484034;
          font: .76rem/2 ui-monospace, "SF Mono", monospace;
          white-space: pre-wrap;
          margin: 0 0 1.4rem;
      }
      .qh-notebook-note {
          color: #702d28;
          font: italic .91rem/1.8 Georgia, "Iowan Old Style", serif;
          margin: 0;
      }
      .qh-notebook-empty-copy {
          margin-top: 5rem;
          color: #81745d;
          font: italic .95rem/1.8 Georgia, "Iowan Old Style", serif;
          text-align: center;
      }
      .qh-notebook-page-no {
          position: absolute;
          right: 1.2rem;
          bottom: .7rem;
          color: #806f55;
          font: .65rem ui-monospace, "SF Mono", monospace;
      }
      @media (max-width: 640px) {
          .qh-notebook-page { min-height: 360px; padding: 1.4rem .9rem 2.5rem 2.2rem; }
          .qh-notebook-page h2 { font-size: 1.35rem; }
      }
      .qh-brief-h {
          font-family: Georgia, serif; font-size: 1.15rem; color: #e8dcc0;
          margin: 1.1rem 0 .35rem 0;
      }
      .qh-brief p {
          font-family: Georgia, serif; font-size: .96rem; line-height: 1.7;
          color: #bdb5ab; margin: 0 0 .75rem 0;
      }
      .qh-brief b { color: #ded5c7; font-weight: 600; }
      .qh-paper .qh-brief b { color: #7d2925; font-weight: 700; }
      .qh-jcat {
          font-family: ui-monospace, monospace; font-size: .7rem;
          letter-spacing: .22em; text-transform: uppercase;
          color: #8c6f3f; margin: 1.3rem 0 .5rem 0;
      }
      div[data-testid="stSidebar"] { background: #121118; }
      .qh-band {
          font-family: ui-monospace, monospace; font-size: .68rem;
          letter-spacing: .13em; text-transform: uppercase; color: #8b8296;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def personalize(body):
    full = st.session_state.name.strip() or "Calloway"
    return body.replace("{name}", full).replace("{first}", full.split()[0])


# A speaking part gets a face. The player does not: the novel is written at
# you, and a portrait of yourself would put a stranger in the second person.
IMAGE_DIR = Path(__file__).resolve().parent.parent / "images"

PORTRAITS = {
    "Harthur": "harthur.png",
    "Crow": "warden.png",
    "Rell": "character.png",
    "Mrs. Anselm": "anselm.png",
    "Physician": "physician.png",
}


@st.cache_data(show_spinner=False)
def portrait_uri(filename):
    """Inline the portrait so it survives unsafe_allow_html. Missing art is
    not worth an exception mid-scene; the line simply renders without a face."""
    try:
        raw = (IMAGE_DIR / filename).read_bytes()
    except OSError:
        return ""
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def block_html(kind, body):
    body = personalize(body)
    if kind == "n":
        return f'<p class="qh-n">{body}</p>'
    if kind == "!":
        return f'<div class="qh-beat">{body}</div>'
    if kind == "doc":
        return f'<div class="qh-doc">{body}</div>'
    speaker = st.session_state.name if kind == "you" else kind
    uri = portrait_uri(PORTRAITS[kind]) if kind in PORTRAITS else ""
    face = f'<img class="qh-face" src="{uri}" alt="">' if uri else ""
    return (
        f'<div class="qh-line">{face}'
        f'<div class="qh-said"><div class="qh-speaker">{speaker}</div>'
        f"<p>{body}</p></div></div>"
    )


def render_blocks(blocks):
    for kind, body in blocks:
        st.markdown(block_html(kind, body), unsafe_allow_html=True)


# --------------------------------------------------------------------------
# PAGE TURNING
# A night is read one paragraph at a time. The consequence of the last choice
# is the front matter of the scene it led to, so it pages first.
# --------------------------------------------------------------------------
# A page holds a beat, not a paragraph. A punchline is short because it is a
# punchline; put a click between it and its setup and the timing dies.
PAGE_SHORT = 15        # a paragraph under this many words cannot open a page
PAGE_MAX_WORDS = 95    # nor may a page grow past this
PAGE_MAX_BLOCKS = 3


def group_pages(blocks):
    pages = []
    force = False
    for kind, body in blocks:
        if kind == "break":           # an author-placed silence
            force = True
            continue
        words = len(body.split())
        page = pages[-1] if pages else None
        held = sum(len(b.split()) for _, b in page) if page else 0
        opens = (
            page is None
            or force
            or len(page) >= PAGE_MAX_BLOCKS
            or held + words > PAGE_MAX_WORDS
            or (kind in ("n", "doc", "!") and words >= PAGE_SHORT)
        )
        # Never strand a one-line setup on a page with nothing to pay it off.
        if opens and not force and page is not None and len(page) == 1 and held < PAGE_SHORT:
            opens = False
        if opens:
            pages.append([(kind, body)])
        else:
            pages[-1].append((kind, body))
        force = False
    return pages


def scene_pages(scene):
    blocks = []
    if st.session_state.log and scene.get("kind") != "ending":
        blocks.extend(st.session_state.log[-1][2])
        blocks.append(("break", ""))   # the consequence closes before the night opens
    blocks.extend(scene.get("text", []))
    return group_pages(blocks)


def current_page(pages):
    """Clamp the turn into range and return it. Guards a mid-scene reload."""
    if not pages:
        st.session_state.page = 0
        return 0
    turn = max(0, min(st.session_state.page, len(pages) - 1))
    st.session_state.page = turn
    return turn


def render_page(pages, turn):
    if not pages:
        return
    held = "".join(block_html(kind, body) for kind, body in pages[turn])
    st.markdown(
        f'<div class="qh-pagemark">{turn + 1:02d} / {len(pages):02d}</div>'
        f'<div class="qh-page">{held}</div>',
        unsafe_allow_html=True,
    )


def turn_page(delta):
    st.session_state.page += delta
    st.rerun()


def render_next_button(label="Next"):
    """The page turn. Sits where the choices will eventually sit."""
    back, fwd = st.columns([1, 3])
    with back:
        if st.button(
            "Back",
            key=f"back_{st.session_state.scene}_{st.session_state.page}",
            use_container_width=True,
            disabled=st.session_state.page == 0,
        ):
            turn_page(-1)
    with fwd:
        if st.button(
            label,
            key=f"next_{st.session_state.scene}_{st.session_state.page}",
            type="primary",
            use_container_width=True,
        ):
            turn_page(1)


@st.dialog("The Journal", width="large")
def show_journal():
    have = st.session_state.journal
    new = st.session_state.journal_show_new
    entries = [
        (key, entry)
        for category in JOURNAL_CATS
        for key, entry in JOURNAL.items()
        if entry["cat"] == category and key in have
    ]
    st.caption(
        f"{len(have)} of {len(JOURNAL)} entries recovered. The Ordinance's text "
        "as the Ordinance gives it. The rest is yours."
    )
    if not have:
        st.info("Nothing yet. It fills as you go.")
        return
    page_count = len(entries)
    last_spread = ((page_count - 1) // 2) * 2
    spread = min((st.session_state.journal_page // 2) * 2, last_spread)
    st.session_state.journal_page = spread
    left_page, right_page = st.columns(2, gap="small")
    for offset, column in enumerate((left_page, right_page)):
        with column:
            page = spread + offset
            if page < page_count:
                key, entry = entries[page]
                new_mark = "  ·  NEW" if key in new else ""
                side = "left" if offset == 0 else "right"
                st.markdown(
                    f'<article class="qh-notebook-page qh-notebook-{side}">'
                    f'<div class="qh-notebook-kicker">{entry["cat"]}{new_mark}</div>'
                    f'<h2>{entry["term"]}</h2>'
                    f'<div class="qh-notebook-official">{entry["official"]}</div>'
                    f'<p class="qh-notebook-note">{entry["note"]}</p>'
                    f'<div class="qh-notebook-page-no">{page + 1:02d} / {page_count:02d}</div>'
                    '</article>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<article class="qh-notebook-page qh-notebook-right">'
                    '<div class="qh-notebook-kicker">Unwritten leaf</div>'
                    '<p class="qh-notebook-empty-copy">No further entry has been recovered.</p>'
                    '</article>',
                    unsafe_allow_html=True,
                )
    previous, counter, next_page = st.columns([1, 1, 1])
    with previous:
        st.button(
            "‹ Previous spread",
            key="journal_previous_spread",
            disabled=spread == 0,
            on_click=turn_journal_spread,
            args=(-1,),
            use_container_width=True,
        )
    with counter:
        spread_count = (page_count + 1) // 2
        st.markdown(
            f'<div class="qh-jcat" style="text-align:center;margin-top:.7rem">'
            f'Spread {spread // 2 + 1} of {spread_count}</div>',
            unsafe_allow_html=True,
        )
    with next_page:
        st.button(
            "Next spread ›",
            key="journal_next_spread",
            disabled=spread >= last_spread,
            on_click=turn_journal_spread,
            args=(1,),
            use_container_width=True,
        )


def turn_journal_spread(direction):
    entry_count = sum(key in st.session_state.journal for key in JOURNAL)
    last_spread = ((entry_count - 1) // 2) * 2
    st.session_state.journal_page = min(
        max(st.session_state.journal_page + direction * 2, 0), last_spread
    )


def journal_button(slot, use_container_width=True):
    count = len(st.session_state.journal_new)
    label = f"📓 Journal — {count} new" if count else "📓 Journal"
    if st.button(
        label,
        key=f"journal_{slot}",
        use_container_width=use_container_width,
        disabled=not st.session_state.journal,
    ):
        # Snapshot before clearing, so the "new" marks survive reruns
        # while the dialog is open.
        st.session_state.journal_show_new = set(st.session_state.journal_new)
        st.session_state.journal_new.clear()
        st.session_state.journal_page = 0
        show_journal()


def band_for(stat, value):
    label = STAT_BANDS[stat][0][1]
    for threshold, text in STAT_BANDS[stat]:
        if value >= threshold:
            label = text
    return label


def take_choice(choice):
    scene = SCENES[st.session_state.scene]
    st.session_state.decision_checkpoints.append(
        {
            "scene": st.session_state.scene,
            "scene_title": scene["title"],
            "choice": choice["label"],
            "stats": dict(st.session_state.stats),
            "flags": set(st.session_state.flags),
            "log": list(st.session_state.log),
        }
    )
    for stat, delta in choice.get("effects", {}).items():
        st.session_state.stats[stat] += delta
    for flag in choice.get("flags", []):
        st.session_state.flags.add(flag)
    st.session_state.log.append(
        (SCENES[st.session_state.scene]["title"], choice["label"], choice.get("outcome", []))
    )
    nxt = choice["next"]
    st.session_state.scene = nxt() if callable(nxt) else nxt
    st.session_state.page = 0
    st.rerun()


def restore_decision_checkpoint(index):
    checkpoint = st.session_state.decision_checkpoints[index]
    st.session_state.scene = checkpoint["scene"]
    st.session_state.stats = dict(checkpoint["stats"])
    st.session_state.flags = set(checkpoint["flags"])
    st.session_state.log = list(checkpoint["log"])
    st.session_state.decision_checkpoints = st.session_state.decision_checkpoints[:index]
    st.session_state.page = 0
    if "decision_checkpoint_select" in st.session_state:
        del st.session_state["decision_checkpoint_select"]
    st.rerun()


# Unlock before anything draws, so the sidebar's "new" count is current.
if st.session_state.started:
    unlock(SCENES[st.session_state.scene].get("journal", []))


# ----------------------------------------------------------------------------
# SIDEBAR — your entry in a book you have never been allowed to read
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🕯️ Quiet Hours")
    st.caption("A horror romance in six nights.")
    journal_button("sidebar")

    if st.session_state.started:
        scene = SCENES[st.session_state.scene]
        st.markdown(f"**{st.session_state.name}**")
        st.caption(f"Third Nail, Ashmoor beat — {scene['act']}")
        st.divider()

        for stat in STAT_ORDER:
            value = st.session_state.stats[stat]
            st.markdown(f"**{STAT_LABELS[stat]}**")
            st.progress(max(0.0, min(value / STAT_MAX[stat], 1.0)))
            st.markdown(
                f'<div class="qh-band">{band_for(stat, value)}</div>',
                unsafe_allow_html=True,
            )
            st.write("")

        if st.session_state.log:
            with st.expander("What you have done so far"):
                for i, (title, label, _) in enumerate(st.session_state.log, 1):
                    st.markdown(f"**{i}. {title}** — {label}")

        checkpoints = st.session_state.decision_checkpoints
        if checkpoints:
            with st.expander("Restore an earlier decision"):
                selected_checkpoint = st.selectbox(
                    "Return to before:",
                    options=range(len(checkpoints)),
                    index=len(checkpoints) - 1,
                    format_func=lambda index: (
                        f"{index + 1}. {checkpoints[index]['scene_title']} — "
                        f"{checkpoints[index]['choice']}"
                    ),
                    key="decision_checkpoint_select",
                )
                if st.button(
                    "Restore decision",
                    key="restore_decision_checkpoint",
                    use_container_width=True,
                ):
                    restore_decision_checkpoint(selected_checkpoint)

        st.divider()

    found = st.session_state.endings_found
    st.markdown(f"**Endings found — {len(found)}/{len(ENDING_ORDER)}**")
    for key in ENDING_ORDER:
        end = SCENES[key]
        if key in found:
            st.markdown(
                f'<span style="color:{end["color"]}">◆</span> {end["title"]}',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("◇ *— — — —*")

    st.divider()
    if st.button("Start over", use_container_width=True):
        fresh_run()
        st.session_state.started = False
        st.rerun()

    with st.expander("Notes & debts"):
        st.caption(
            "Borrowed openly from George Orwell's **Nineteen Eighty-Four** "
            "(the total ledger, the interrogation that wants a word and not a "
            "fact, the Quiet Room, the colleague informed on by his own wife) "
            "and Franz Kafka's **The Metamorphosis** (the voice going first, "
            "the morning the body stops being yours, the iron grown over in a "
            "back that cannot reach it, and the sweeping-out afterward). The "
            "self-cross-examining narration also owes a thematic debt to Fyodor "
            "Dostoevsky's **Notes from Underground**."
        )


# ----------------------------------------------------------------------------
# THE BRIEFING — the same story in plain words, for the start page.
# Everything above this line is written in the story's voice. This part is
# not: it is here so that nobody has to decode the prose to know what the
# game is about or what the five meters are doing.
# ----------------------------------------------------------------------------
THE_WORLD = """
<p>The city is <b>Vantage</b>. There is one enormous book, the <b>Registry</b>,
listing everybody who exists. If your name is in it you are a person; if it is
not, you are not. That is not a figure of speech — it is the legal definition.</p>
<p>The <b>Ordinance of Quiet Hours</b> is the police force that hunts monsters
hiding as human beings. Ordinary people are frightened all the time and inform on
each other constantly. Monsters are killed in the street, and crowds turn out to
watch.</p>
"""

THE_CHARACTERS = """
<p><b>You</b> — a monster hunter, twenty-eight, a man. You carry an iron nail and
a lamp that shows what is hiding under somebody's face. Since you were seventeen
you have drunk a weekly dose called <b>the Draught</b>, which is the only reason
the lamp works.</p>
<p><b>Harthur</b> — the bookbinder you are sent to investigate. He is a monster.
He has also spent twenty years quietly scraping people's names out of the
Registry to save them, four hundred and six so far, while the Ordinance takes the
credit for the falling numbers.</p>
"""

THE_TRAP = """
<p><b>The lamp burns inside your own eyes.</b> So nothing it has ever shown you
can be proved to anybody else — and your Warden keeps pointing out, correctly,
that the Draught makes hunters hallucinate, with sixty-one documented varieties
on a printed page.</p>
<p>So you spend six nights trying to establish whether he is real. And every time
you reach for hard evidence — swabbing his blood, bringing a colleague to look at
him — he notices, and something in him closes.</p>
<p><b>Proving he is real costs you him.</b> That is the whole trap.</p>
"""

METERS = [
    ("Harthur", "How attached he is to you.", "He is being polite", "He will not be able to let go"),
    ("The Pull", "How much you want the danger.", "You are doing your job", "You want to be taken"),
    ("What You Can Prove", "Physical evidence in your pockets.", "Nothing at all", "Something they would have to answer"),
    ("Ordinance Interest", "How closely your employers are watching.", "Unremarkable", "Scheduled"),
    ("Conformity of the Body", "How far you have turned into one of them.", "Within tolerance", "Disposable"),
]

# Door -> (ending title, what it needs). Order matches the resolvers.
ROUTES = {
    "Open the door": [
        ("No Such Man", "With nothing physical to prove, the Ordinance decides Harthur was a Draught hallucination. They take your lamp, taper you off the drug, and send you to recover in a ward; you are left unsure whether he was real. **Condition:** You never find evidence stronger than what only your own eyes can tell you. This overrides every other ending on any route."),
        ("Verminous", "The Draught's effects overtake your body. The Ordinance confines you and waits for the transformation to finish, then records your disposal as routine. Harthur is left behind, still waiting for you. **Condition:** Your body reaches **Disposable**."),
        ("The Hunter's Mercy", "You kill Harthur yourself to spare him the Quiet Room. The Ordinance praises and promotes you, but soon you discover the iron is growing into your own back. **Condition:** You drew your iron on Night Four, **or** Harthur's attachment never rose above *He is paying attention*."),
        ("The Quiet Room", "Harthur is taken alive, and under pressure you call him a monster. The Ordinance rewards your testimony with a commendation and a new district; you keep your post, but the grief stays with you. **Condition:** None of the earlier Open the door conditions apply."),
    ],
    "Run to the Mire": [
        ("No Such Man", "With nothing physical to prove, the Ordinance decides Harthur was a Draught hallucination. They take your lamp, taper you off the drug, and send you to recover in a ward; you are left unsure whether he was real. **Condition:** You never find evidence stronger than what only your own eyes can tell you. This overrides every other ending on any route."),
        ("Two Bodies, One Ledger", "You stop running and let the change finish. Harthur stays beside you through the transformation, and together you join the hidden lives beneath the city, beyond the Registry's definition of personhood. **Condition:** Your body reaches **Disposable** and Harthur's attachment reaches **He is keeping you**."),
        ("Verminous", "You reach the Mire without Harthur. The Draught's effects overtake your body, and the Ordinance confines you until the transformation is complete; Harthur remains behind, waiting with two cups. **Condition:** Your body reaches **Disposable**, but Harthur has not reached **He is keeping you**."),
        ("The Amended Name", "Harthur erases both your names from the Registry. In the Mire, you choose to let him set aside his human face, and the two of you disappear from the Ordinance's records together. **Condition:** Harthur is keeping you, the Pull has reached **You keep going back**, and your body is still short of **Disposable**."),
        ("A Clean Report", "You stop on the third step and let Harthur go alone. You keep your post and your life, but the change in your body continues in private, and you carry the loss back to the Ashmoor beat. **Condition:** None of the earlier Run to the Mire conditions apply."),
    ],
    "Burn the Registry": [
        ("No Such Man", "With nothing physical to prove, the Ordinance decides Harthur was a Draught hallucination. They take your lamp, taper you off the drug, and send you to recover in a ward; you are left unsure whether he was real. **Condition:** You never find evidence stronger than what only your own eyes can tell you. This overrides every other ending on any route."),
        ("Both Names Struck", "You and Harthur burn the Registry together. You die in the fire, but the city's central record is gone, leaving the Ordinance unable to prove who belongs in it. **Condition:** Harthur's attachment has reached **He is keeping you**."),
        ("Ash and Nothing", "You burn the Registry alone, but its nightly duplicates survive and the Ordinance rebuilds the records. You are taken, and Harthur is captured; the 406 people he erased remain untraceable, while the new ledger writes your names together. **Condition:** Harthur has not yet reached **He is keeping you**."),
    ],
}


# ----------------------------------------------------------------------------
# TITLE SCREEN
# ----------------------------------------------------------------------------
if not st.session_state.started:
    st.markdown(
        '<div class="qh-title-screen">'
        '<header class="qh-start-hero">'
        '<div class="qh-start-kicker">Vantage City // Incident File 44-118-C</div>'
        '<h1>Quiet Hours</h1>'
        '<p class="qh-start-subtitle">A horror romance in six nights. The Registry decides who is a person. You have been sent to correct its mistake.</p>'
        '<div class="qh-start-stamp">Third Nail // Ashmoor Beat // Case Open</div>'
        '</header>'
        '<section class="qh-paper">'
        '<div class="qh-paper-label">A notice from the Ordinance</div>'
        '<p class="qh-opening-copy">There is a book in this city with ninety thousand names in it, and the book decides which of them are people.</p>'
        '<p class="qh-opening-copy">You carry a nail for the ones it decides against. There is a queue outside the Ordinance house every morning of people who have come to help you. There is chalk going up on doors that nobody official chalked. On Marrow Street this afternoon a woman lifted her boy onto her shoulders so that he could see over the hats.</p>'
        '<div class="qh-opening-doc">THE ORDINANCE OF QUIET HOURS\nA MONSTER IS A THING THE LEDGER HAS NOT YET NAMED.\nMERCY IS MURDER, DEFERRED.\nYOU ARE NOT BEING WATCHED. YOU ARE BEING KEPT.</div>'
        '</section>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr class="qh-rule">', unsafe_allow_html=True)

    # --- the same thing again, in plain words -------------------------------
    w, c = st.columns(2)
    with w:
        st.markdown(
            f'<section class="qh-paper"><div class="qh-paper-label">The world</div>'
            f'<div class="qh-brief">{THE_WORLD}</div></section>',
            unsafe_allow_html=True,
        )
    with c:
        st.markdown(
            f'<section class="qh-paper"><div class="qh-paper-label">The two characters</div>'
            f'<div class="qh-brief">{THE_CHARACTERS}</div></section>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<section class="qh-paper"><div class="qh-paper-label">The trap</div>'
        f'<div class="qh-brief">{THE_TRAP}</div></section>',
        unsafe_allow_html=True,
    )

    with st.expander("🔒  Routes explained  —  spoilers"):
        st.caption(
            "Nine endings. Night Six asks you to pick one of three doors; the "
            "five meters decide which room is behind it. Each entry summarizes "
            "what happens and gives the condition that leads to it."
        )
        for tab, (door, rows) in zip(st.tabs(list(ROUTES)), ROUTES.items()):
            with tab:
                for title, need in rows:
                    end = SCENES[
                        next(k for k in ENDING_ORDER if SCENES[k]["title"] == title)
                    ]
                    st.markdown(
                        f'<span style="color:{end["color"]}">◆</span> '
                        f'**{title}** — {need}',
                        unsafe_allow_html=True,
                    )
        st.caption(
            "Read top to bottom: the first line whose condition you meet is the "
            "ending you get."
        )

    st.markdown(
        '<section class="qh-paper"><div class="qh-paper-label">The five meters</div>'
        '<table><thead><tr><th>Meter</th><th>What it tracks</th><th>Runs from</th><th>Up to</th></tr></thead>'
        f'<tbody>{"".join(f"<tr><td><strong>{name}</strong></td><td>{description}</td><td>{low}</td><td>{high}</td></tr>" for name, description, low, high in METERS)}</tbody></table>'
        '</section>',
        unsafe_allow_html=True,
    )
    st.caption("They sit in the sidebar the whole way through. Watch them.")

    st.markdown('<hr class="qh-rule">', unsafe_allow_html=True)
    st.text_input("Your name, for the file:", key="name")
    st.caption("The Ordinance files you in full. Rell will use your first name.")
    if st.button("Begin — Night One", type="primary", use_container_width=True):
        fresh_run()
        st.session_state.started = True
        st.rerun()
    st.stop()


# ----------------------------------------------------------------------------
# SCENE
# ----------------------------------------------------------------------------
scene = SCENES[st.session_state.scene]

st.markdown(f'<div class="qh-act">{scene["act"]}</div>', unsafe_allow_html=True)

if scene.get("kind") == "ending":
    st.session_state.endings_found.add(st.session_state.scene)
    color = scene["color"]
    st.markdown(
        f'<div class="qh-end" style="border-color:{color};background:{color}14;">'
        f'<div class="qh-act">An ending</div>'
        f'<h2 style="color:{color};">{scene["title"]}</h2></div>',
        unsafe_allow_html=True,
    )
    pages = scene_pages(scene)
    turn = current_page(pages)
    render_page(pages, turn)
    st.markdown('<hr class="qh-rule">', unsafe_allow_html=True)

    if turn < len(pages) - 1:
        render_next_button()
        st.stop()

    s = st.session_state.stats
    lines = "\n".join(
        f'{STAT_LABELS[k] + " ":.<30}{band_for(k, s[k])}' for k in STAT_ORDER
    )
    st.markdown(
        f'<div class="qh-doc">CLOSING ENTRY — {personalize("{name}").upper()}\n'
        f"{lines}\n"
        f'{"Endings recovered ":.<30}{len(st.session_state.endings_found)} of {len(ENDING_ORDER)}</div>',
        unsafe_allow_html=True,
    )

    remaining = len(ENDING_ORDER) - len(st.session_state.endings_found)
    if remaining:
        st.caption(f"{remaining} more ways this goes. The book is still open.")
    else:
        st.caption("All nine. There was never a clean one. That was the point.")

    again, jrnl = st.columns([2, 1])
    with again:
        if st.button("Again, from the first knock", type="primary", use_container_width=True):
            fresh_run()
            st.rerun()
    with jrnl:
        journal_button("ending")
    st.stop()

st.markdown(f'<h1 class="qh-title">{scene["title"]}</h1>', unsafe_allow_html=True)

_, jcol = st.columns([2, 1])
with jcol:
    journal_button("scene")

# One paragraph to a page, the consequence of the last choice first.
pages = scene_pages(scene)
turn = current_page(pages)
render_page(pages, turn)

st.markdown('<hr class="qh-rule">', unsafe_allow_html=True)

# The choices wait on the last page of the night.
if turn < len(pages) - 1:
    render_next_button()
else:
    for i, choice in enumerate(scene["choices"]):
        if st.button(choice["label"], key=f"{st.session_state.scene}_{i}", use_container_width=True):
            take_choice(choice)
        st.caption(choice["detail"])
    if len(pages) > 1:
        st.markdown('<hr class="qh-rule">', unsafe_allow_html=True)
        if st.button(
            "Back",
            key=f"back_{st.session_state.scene}_{turn}",
            use_container_width=True,
        ):
            turn_page(-1)
