import unittest
from nlp.embeddings import cosine, embed_with_optional_model
from nlp.extractors import extract_age, extract_education, extract_gender, extract_income, extract_location
from nlp.life_events import detect_life_events
from nlp.needs import detect_needs
from nlp.pipeline import parse_query


class TestNLP(unittest.TestCase):
    def test_extract_attributes_age_and_location(self):
        text = "I am a 22-year-old student from Chennai, Tamil Nadu with family income of 150000"
        age = extract_age(text)
        state, district = extract_location(text)
        income = extract_income(text)
        education = extract_education(text)

        self.assertEqual(age, 22)
        self.assertEqual(state, "Tamil Nadu")
        self.assertEqual(district, "Chennai")
        self.assertEqual(income, 150000)
        self.assertEqual(education, "Student")

    def test_extract_attributes_gender_and_needs(self):
        text = "Female farmer aged 35 years living in Madurai seeking agriculture loans"
        gender = extract_gender(text)
        age = extract_age(text)
        state, district = extract_location(text)

        self.assertEqual(gender, "female")
        self.assertEqual(age, 35)
        self.assertEqual(state, "Tamil Nadu")
        self.assertEqual(district, "Madurai")

    def test_detect_needs(self):
        text = "I need medical help and financial grant for hospital surgery"
        needs = detect_needs(text, {})
        need_codes = [n["need_code"] for n in needs]
        self.assertIn("healthcare", need_codes)
        self.assertIn("financial_assistance", need_codes)

    def test_detect_life_events(self):
        text = "I just graduated from engineering college and lost my job"
        events = detect_life_events(text)
        event_codes = [e["event_code"] for e in events]
        self.assertIn("graduation", event_codes)
        self.assertIn("job_loss", event_codes)

    def test_parse_query_pipeline(self):
        query = "I am a 19 year old girl student in Coimbatore looking for scholarship"
        result = parse_query(query)
        self.assertEqual(result["locale"], "en")
        self.assertEqual(result["fields"]["age"], 19)
        self.assertEqual(result["fields"]["gender"], "female")
        self.assertEqual(result["fields"]["district"], "Coimbatore")
        self.assertEqual(result["fields"]["state"], "Tamil Nadu")
        needs = [n["need_code"] for n in result["needs"]]
        self.assertIn("education", needs)

    def test_embeddings_similarity(self):
        v1, _ = embed_with_optional_model("Tamil Nadu higher education scholarship for students")
        v2, _ = embed_with_optional_model("College student scholarship tuition fee support in Tamil Nadu")
        v3, _ = embed_with_optional_model("Tractor subsidy for sugarcane agriculture farming")

        sim_1_2 = cosine(v1, v2)
        sim_1_3 = cosine(v1, v3)

        self.assertGreater(sim_1_2, sim_1_3)


if __name__ == "__main__":
    unittest.main()
