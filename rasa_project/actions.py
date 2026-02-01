# actions/actions.py
from typing import Any, Text, Dict, List, Optional, Tuple
import re
import requests
import time

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.types import DomainDict

# -----------------------------
# Nominatim (NO API KEY needed)
# -----------------------------
NOMINATIM_BASE = "https://nominatim.openstreetmap.org"

# IMPORTANT:
# 1) Nominatim requires a proper User-Agent identifying your app.
# 2) Put YOUR real email below (recommended by their usage policy).
# Replace these two values before you run in production.
NOMINATIM_CONTACT_EMAIL = "ddeepak752@gmail.com"
NOMINATIM_HEADERS = {
    "User-Agent": f"crisis-response-chatbot/1.0 (BSBI assignment; contact: {NOMINATIM_CONTACT_EMAIL})"
}


def nominatim_geocode(query: str) -> Optional[Tuple[str, float, float]]:
    """
    Geocode a text location -> (display_name, lat, lon) or None.
    Uses Nominatim Search API.
    """
    try:
        # Gentle pacing (helps reduce rate-limit issues)
        time.sleep(0.1)

        params = {
            "format": "json",
            "q": query,
            "limit": 1,
            "addressdetails": 1,
            "email": NOMINATIM_CONTACT_EMAIL,
        }
        r = requests.get(
            f"{NOMINATIM_BASE}/search",
            params=params,
            headers=NOMINATIM_HEADERS,
            timeout=8,
        )
        if r.status_code != 200:
            return None
        data = r.json() or []
        if not data:
            return None

        top = data[0]
        display_name = top.get("display_name", query)
        lat = float(top.get("lat"))
        lon = float(top.get("lon"))
        return display_name, lat, lon
    except Exception:
        return None


def nominatim_find_shelters(lat: float, lon: float, radius_km: float = 5.0, limit: int = 5) -> List[str]:
    """
    Best-effort shelter lookup around a coordinate using Nominatim Search with a bounded viewbox.
    NOTE: OSM tagging varies by city, so this is "best effort".
    """
    try:
        # Rough degree conversion for bounding box
        dlat = radius_km / 111.0
        dlon = radius_km / 111.0

        left = lon - dlon
        right = lon + dlon
        top = lat + dlat
        bottom = lat - dlat

        queries = [
            "emergency shelter",
            "evacuation center",
            "community center",
            "shelter",
        ]

        results: List[str] = []
        for q in queries:
            # Gentle pacing
            time.sleep(0.1)

            params = {
                "format": "json",
                "q": q,
                "limit": limit,
                "addressdetails": 1,
                "bounded": 1,
                "viewbox": f"{left},{top},{right},{bottom}",
                "email": NOMINATIM_CONTACT_EMAIL,
            }
            r = requests.get(
                f"{NOMINATIM_BASE}/search",
                params=params,
                headers=NOMINATIM_HEADERS,
                timeout=8,
            )
            if r.status_code != 200:
                continue

            data = r.json() or []
            for item in data:
                name = item.get("display_name")
                if name and name not in results:
                    results.append(name)
                if len(results) >= limit:
                    return results

        return results[:limit]
    except Exception:
        return []


# -----------------------------
# Actions
# -----------------------------
class ActionRestart(Action):
    def name(self) -> Text:
        return "action_restart"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(
            text="🔄 Chat restarted. Hi! I'm the Crisis Response Assistant. If this is life-threatening, call your local emergency number now. Type: emergency to begin."
        )
        return [
            SlotSet("crisis_type", None),
            SlotSet("location", None),
            SlotSet("location_verified", None),
            SlotSet("location_lat", None),
            SlotSet("location_lon", None),
            SlotSet("shelter_suggestions", None),
            SlotSet("people_count", None),
            SlotSet("vulnerability", None),
            SlotSet("mobility_status", None),
            SlotSet("injury_status", None),
            SlotSet("risk_level", None),
            SlotSet("risk_score", None),
            SlotSet("vulnerability_summary", None),
            SlotSet("requested_slot", None),
        ]


class ActionGreetAndRestart(Action):
    def name(self) -> Text:
        return "action_greet_and_restart"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_greet")
        return []


class ActionClearSlots(Action):
    def name(self) -> Text:
        return "action_clear_slots"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        return [
            SlotSet("crisis_type", None),
            SlotSet("location", None),
            SlotSet("location_verified", None),
            SlotSet("location_lat", None),
            SlotSet("location_lon", None),
            SlotSet("shelter_suggestions", None),
            SlotSet("people_count", None),
            SlotSet("vulnerability", None),
            SlotSet("mobility_status", None),
            SlotSet("injury_status", None),
            SlotSet("risk_level", None),
            SlotSet("risk_score", None),
            SlotSet("vulnerability_summary", None),
        ]


class ActionSetCrisisType(Action):
    def name(self) -> Text:
        return "action_set_crisis_type"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message.get("intent", {}).get("name")

        mapping = {
            "report_earthquake": "earthquake",
            "report_flood": "flood",
            "report_fire": "fire",
            "report_power_outage": "power_outage",
        }

        crisis_type = mapping.get(intent)
        if crisis_type:
            # Clear previous assessment data on new crisis type
            return [
                SlotSet("crisis_type", crisis_type),
                SlotSet("location", None),
                SlotSet("location_verified", None),
                SlotSet("location_lat", None),
                SlotSet("location_lon", None),
                SlotSet("shelter_suggestions", None),
                SlotSet("people_count", None),
                SlotSet("vulnerability", None),
                SlotSet("mobility_status", None),
                SlotSet("injury_status", None),
                SlotSet("risk_level", None),
                SlotSet("risk_score", None),
                SlotSet("vulnerability_summary", None),
            ]
        return []


# -----------------------------
# Form Validation
# -----------------------------
class ValidateCrisisForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_crisis_form"

    def validate_location(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if not slot_value or len(str(slot_value).strip()) == 0:
            return {
                "location": None,
                "location_verified": False,
                "location_lat": None,
                "location_lon": None,
            }

        raw = str(slot_value).strip()
        location_text = raw.lower().strip()

        vague_locations = {
            "home", "house", "apartment", "work", "office", "school", "here", "inside", "outside",
            "not sure", "dont know", "don't know", "unsure", "somewhere", "around", "nearby",
            "close", "far", "there", "this place", "my place", "upstairs", "downstairs",
            "room", "building", "car", "vehicle",
        }

        if location_text in vague_locations:
            dispatcher.utter_message(
                text=f"'{raw}' is too vague. Please provide: City + Landmark (e.g., 'Berlin, Alexanderplatz')."
            )
            return {"location": None, "location_verified": False, "location_lat": None, "location_lon": None}

        if location_text.isdigit() or len(location_text) < 4:
            dispatcher.utter_message(
                text=f"'{raw}' seems incomplete. Please provide full location (City + Landmark)."
            )
            return {"location": None, "location_verified": False, "location_lat": None, "location_lon": None}

        # ✅ Safe fallback: accept city-only even if Nominatim temporarily fails
        known_cities = {
            "berlin", "munich", "muenchen", "hamburg", "frankfurt", "frankfurt am main",
            "cologne", "koeln", "düsseldorf", "dusseldorf", "stuttgart", "leipzig",
            "bremen", "dresden", "hannover", "nuremberg", "nürnberg", "nurnberg",
        }

        # Verify via Nominatim
        geo = nominatim_geocode(raw)
        if geo:
            display_name, lat, lon = geo
            return {
                "location": display_name,
                "location_verified": True,
                "location_lat": lat,
                "location_lon": lon,
            }

        # If it looks like a known city, accept without warning (prevents confusion)
        if location_text in known_cities:
            return {
                "location": raw.title(),
                "location_verified": False,
                "location_lat": None,
                "location_lon": None,
            }

        # Accept but gently request more detail
        dispatcher.utter_message(
            text="📍 I could not verify that location on the map. Please add a landmark/street (e.g., 'Berlin, Alexanderplatz')."
        )
        return {"location": raw, "location_verified": False, "location_lat": None, "location_lon": None}

    def validate_people_count(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if not slot_value:
            return {"people_count": None}
        try:
            count = int(str(slot_value).strip())
            if count > 0:
                return {"people_count": str(count)}
            dispatcher.utter_message(text="Please provide a number greater than 0.")
            return {"people_count": None}
        except ValueError:
            dispatcher.utter_message(text="Please provide a number (e.g., 1, 2, 3).")
            return {"people_count": None}

    def validate_vulnerability(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if not slot_value:
            return {"vulnerability": None}
        v = str(slot_value).lower().strip()
        if v in ["hi", "hello", "hey", "restart", "help", "what", "when", "where"]:
            dispatcher.utter_message(
                text="Please answer: Any vulnerable people? (children / elderly / pregnant / medical needs / none)"
            )
            return {"vulnerability": None}
        return {"vulnerability": str(slot_value).strip()}

    def validate_mobility_status(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if not slot_value:
            return {"mobility_status": None}
        m = str(slot_value).lower().strip()
        if m in ["hi", "hello", "hey", "restart", "help", "what", "when", "where"]:
            dispatcher.utter_message(text="Please answer: Can you move to a safer place? (yes / no / unsure)")
            return {"mobility_status": None}

        if m in ["yes", "yeah", "y", "can move", "able to move"]:
            dispatcher.utter_message(text="✅ Good! Move to a safer place now if possible. Then we continue.")
            return {"mobility_status": "yes"}
        if m in ["no", "n", "cannot move", "can't move", "unable", "stuck", "trapped"]:
            dispatcher.utter_message(text="🛑 Stay where you are. Do NOT attempt to move if unsafe.")
            return {"mobility_status": "no"}
        if m in ["unsure", "not sure", "dont know", "don't know", "maybe", "uncertain"]:
            dispatcher.utter_message(text="⚠️ Only move if you are sure it is safer. When in doubt, stay put.")
            return {"mobility_status": "unsure"}

        return {"mobility_status": str(slot_value).strip()}

    def validate_injury_status(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if not slot_value:
            return {"injury_status": None}
        i = str(slot_value).lower().strip()

        if i in ["hi", "hello", "hey", "restart", "help", "what", "when", "where"]:
            dispatcher.utter_message(text="Please answer: Are you or anyone with you injured? (yes / no / unsure)")
            return {"injury_status": None}

        if i in ["yes", "y", "injured", "hurt", "bleeding", "wounded"]:
            dispatcher.utter_message(text="🚑 Injuries reported. Do NOT move injured persons unless immediate danger.")
            return {"injury_status": "yes"}
        if i in ["no", "n", "none", "not injured", "fine", "ok", "okay"]:
            dispatcher.utter_message(text="✅ No injuries reported. Continuing assessment.")
            return {"injury_status": "no"}
        if i in ["unsure", "not sure", "dont know", "don't know", "maybe", "unclear"]:
            dispatcher.utter_message(text="🔍 Check injuries carefully (bleeding, breathing, consciousness).")
            return {"injury_status": "unsure"}

        return {"injury_status": str(slot_value).strip()}


# -----------------------------
# Risk Assessment + Shelter Suggestions
# -----------------------------
class ActionCalculateRiskLevel(Action):
    def name(self) -> Text:
        return "action_calculate_risk_level"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        crisis_type = tracker.get_slot("crisis_type") or "unknown"
        mobility_status = str(tracker.get_slot("mobility_status") or "").lower().strip()
        injury_status = str(tracker.get_slot("injury_status") or "").lower().strip()
        people_count = int(tracker.get_slot("people_count") or 1)
        vulnerability_text = str(tracker.get_slot("vulnerability") or "").lower()

        # Parse vulnerability text
        children_count = 0
        elderly_count = 0
        pregnant_count = 0
        medical_count = 0

        child_matches = re.findall(r"(\d+)\s*(?:child|kid|baby|infant|children|kids)", vulnerability_text)
        if child_matches:
            children_count = sum(int(x) for x in child_matches)
        elif any(w in vulnerability_text for w in ["child", "kid", "baby", "infant", "children", "kids"]):
            children_count = 1

        elderly_matches = re.findall(r"(\d+)\s*(?:elderly|old|senior|grandparent)", vulnerability_text)
        if elderly_matches:
            elderly_count = sum(int(x) for x in elderly_matches)
        elif any(w in vulnerability_text for w in ["elderly", "old", "senior", "grandparent"]):
            elderly_count = 1

        pregnant_matches = re.findall(r"(\d+)\s*(?:pregnant|expecting)", vulnerability_text)
        if pregnant_matches:
            pregnant_count = sum(int(x) for x in pregnant_matches)
        elif any(w in vulnerability_text for w in ["pregnant", "expecting"]):
            pregnant_count = 1

        medical_matches = re.findall(r"(\d+)\s*(?:medical|disability|disabled|sick|asthma)", vulnerability_text)
        if medical_matches:
            medical_count = sum(int(x) for x in medical_matches)
        elif any(w in vulnerability_text for w in ["medical", "disability", "disabled", "sick", "asthma"]):
            medical_count = 1

        total_vulnerable = children_count + elderly_count + pregnant_count + medical_count

        details = []
        if children_count:
            details.append(f"{children_count} children")
        if elderly_count:
            details.append(f"{elderly_count} elderly")
        if pregnant_count:
            details.append(f"{pregnant_count} pregnant")
        if medical_count:
            details.append(f"{medical_count} medical needs")
        vulnerability_summary = ", ".join(details) if details else "none"
        if total_vulnerable > 0:
            vulnerability_summary += f" ({total_vulnerable} vulnerable individuals)"

        # Risk scoring
        risk_score = 0
        crisis_risk = {"earthquake": 30, "fire": 30, "flood": 25, "power_outage": 15}
        risk_score += crisis_risk.get(crisis_type, 20)

        if people_count >= 5:
            risk_score += 20
        elif people_count >= 3:
            risk_score += 10
        elif people_count == 2:
            risk_score += 5

        risk_score += children_count * 15
        risk_score += elderly_count * 15
        risk_score += pregnant_count * 15
        risk_score += medical_count * 15

        if total_vulnerable >= 3:
            risk_score += 15
        elif total_vulnerable >= 2:
            risk_score += 10

        if mobility_status in ["no", "can't move", "cannot move", "stuck", "unable", "trapped"]:
            risk_score += 20
        elif mobility_status in ["unsure", "not sure", "maybe", "uncertain"]:
            risk_score += 10

        if injury_status in ["yes", "injured", "hurt", "bleeding", "wounded"]:
            risk_score += 25
        elif injury_status in ["unsure", "not sure", "maybe", "unclear"]:
            risk_score += 10

        risk_score = min(risk_score, 100)

        if risk_score >= 76:
            risk_level = "CRITICAL"
        elif risk_score >= 51:
            risk_level = "HIGH"
        elif risk_score >= 26:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Shelter suggestions if we have verified coordinates
        shelters_list: List[str] = []
        location_verified = bool(tracker.get_slot("location_verified"))
        lat = tracker.get_slot("location_lat")
        lon = tracker.get_slot("location_lon")

        if location_verified and lat is not None and lon is not None:
            shelters_list = nominatim_find_shelters(float(lat), float(lon), radius_km=5.0, limit=5)

        if shelters_list:
            shelters_text = "🏠 Nearby shelter / safe places (approx):\n" + "\n".join([f"- {s}" for s in shelters_list])
        else:
            shelters_text = "🏠 Nearby shelters: Not found automatically (try adding a more specific landmark)."

        msg = (
            f"📋 CRISIS ASSESSMENT COMPLETE:\n"
            f"Crisis Type: {crisis_type} | Location: {tracker.get_slot('location')} | People: {people_count}\n"
            f"Vulnerabilities: {vulnerability_summary} | Mobility: {mobility_status} | Injuries: {injury_status}\n\n"
            f"🎯 RISK LEVEL: {risk_level} | 📊 Risk Score: {risk_score}/100\n"
            f"📋 Risk Levels: • 0-25: LOW • 26-50: MEDIUM • 51-75: HIGH • 76-100: CRITICAL\n\n"
            f"{shelters_text}\n"
        )

        dispatcher.utter_message(text=msg)

        return [
            SlotSet("risk_level", risk_level),
            SlotSet("risk_score", float(risk_score)),
            SlotSet("vulnerability_summary", vulnerability_summary),
            SlotSet("shelter_suggestions", "\n".join(shelters_list) if shelters_list else ""),
        ]


class ActionFinishAndGuide(Action):
    def name(self) -> Text:
        return "action_finish_and_guide"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        crisis_type = tracker.get_slot("crisis_type") or "unknown"
        mobility_status = str(tracker.get_slot("mobility_status") or "")
        injury_status = str(tracker.get_slot("injury_status") or "")
        risk_level = tracker.get_slot("risk_level") or "MEDIUM"

        if risk_level in ["CRITICAL", "HIGH"]:
            emergency_header = f"🚨 {risk_level} RISK SITUATION 🚨\n\n⚠️ STRONGLY RECOMMEND CALLING EMERGENCY SERVICES: 112/911\n\n"
        else:
            emergency_header = f"ℹ️ {risk_level} Risk Assessment\n\n"

        if crisis_type == "earthquake":
            msg = (
                "🏠 EARTHQUAKE SAFETY PROTOCOL:\n"
                "1) DROP, COVER, HOLD ON - Get under sturdy furniture\n"
                "2) Stay away from windows and heavy objects\n"
                "3) If outdoors, move away from buildings\n"
                "4) After shaking stops, check for injuries and hazards\n"
                "5) Expect aftershocks - be prepared to Drop/Cover/Hold again\n"
                "6) Evacuate if building shows structural damage"
            )
        elif crisis_type == "flood":
            msg = (
                "🌊 FLOOD SAFETY PROTOCOL:\n"
                "1) Move to highest ground immediately\n"
                "2) NEVER walk through moving water\n"
                "3) Turn off electricity if safe\n"
                "4) Avoid driving through flood water\n"
                "5) Listen to evacuation orders\n"
                "6) Stay away from storm drains"
            )
        elif crisis_type == "fire":
            msg = (
                "🔥 FIRE SAFETY PROTOCOL:\n"
                "1) GET OUT IMMEDIATELY if you see flames or heavy smoke\n"
                "2) Crawl low under smoke\n"
                "3) Feel doors before opening\n"
                "4) NEVER use elevators\n"
                "5) Once outside, stay outside and call emergency services\n"
                "6) If trapped, seal cracks and signal for help"
            )
        elif crisis_type == "power_outage":
            msg = (
                "⚡ POWER OUTAGE SAFETY PROTOCOL:\n"
                "1) Use flashlights only\n"
                "2) Keep refrigerator/freezer closed\n"
                "3) Disconnect appliances to prevent surge damage\n"
                "4) Stay away from downed power lines\n"
                "5) If you rely on medical equipment, contact emergency services\n"
                "6) Use generators outside only"
            )
        else:
            msg = "📋 General emergency protocol: If life-threatening, call emergency services immediately."

        if "no" in mobility_status.lower() or "can't" in mobility_status.lower():
            msg += "\n\n🛑 MOBILITY RESTRICTION: Stay in place. Help is coming to you."
        elif "yes" in mobility_status.lower():
            msg += "\n\n✅ MOBILITY CONFIRMED: Follow evacuation procedures if needed."

        if "yes" in injury_status.lower():
            msg += "\n\n🚑 INJURIES REPORTED: Do not move injured persons unless immediate danger."
        elif "no" in injury_status.lower():
            msg += "\n\n✅ NO INJURIES: Continue standard protocols."

        dispatcher.utter_message(text=emergency_header + msg)
        return []


class ActionFallbackRouter(Action):
    """
    Single fallback router for your assignment pipeline.
    - If user types something during crisis flow that doesn't match expected,
      we guide them back based on requested_slot or crisis stage.
    - This action is referenced by RulePolicy fallback_action_name.
    """

    def name(self) -> Text:
        return "action_fallback_router"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        requested_slot = tracker.get_slot("requested_slot")
        active_loop = tracker.active_loop.get("name") if tracker.active_loop else None
        crisis_type = tracker.get_slot("crisis_type")

        # Not in emergency flow yet
        if not crisis_type and active_loop is None:
            dispatcher.utter_message(
                text="I didn't understand that. If this is an emergency, type: emergency"
            )
            return []

        # If form is active, re-ask the right question
        if active_loop == "crisis_form":
            if requested_slot == "location":
                dispatcher.utter_message(response="utter_ask_location")
                return []
            if requested_slot == "people_count":
                dispatcher.utter_message(response="utter_ask_people_count")
                return []
            if requested_slot == "vulnerability":
                dispatcher.utter_message(response="utter_ask_vulnerability")
                return []
            if requested_slot == "mobility_status":
                dispatcher.utter_message(response="utter_ask_mobility_status")
                return []
            if requested_slot == "injury_status":
                dispatcher.utter_message(response="utter_ask_injury_status")
                return []

            dispatcher.utter_message(
                text="I didn't understand. Please answer the current question so I can continue the assessment."
            )
            return []

        # Crisis started but no form active
        dispatcher.utter_message(response="utter_offer_more_steps")
        return []
