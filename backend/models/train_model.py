"""
Model Training Script for Fake News Classifier.
Trains an NLP text classifier using TF-IDF n-grams and calibrated linear classification.
"""

import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# High quality curated training dataset covering real news, disinformation, hoaxes, clickbait, and satire
DATASET = [
    # --- REAL NEWS SAMPLES (Label 1 = Genuine) ---
    (
        "Federal Reserve maintains interest rates following steady economic growth",
        "The Federal Reserve announced on Wednesday that benchmark interest rates would remain unchanged at their current target range. Federal Reserve Chair Jerome Powell stated during a press conference in Washington that inflation data showed consistent progress toward the central bank's two percent target, while labor market indicators remained resilient. Official economic reports released by the Department of Labor showed consumer prices rose modestly over the past quarter.",
        1
    ),
    (
        "World Health Organization approves new pediatric malaria vaccine rollout",
        "The World Health Organization confirmed the prequalification of a new pediatric malaria vaccine, marking a major milestone in global public health. According to clinical trial data published in The Lancet medical journal, the vaccine demonstrated 77 percent efficacy in clinical trials conducted across four African nations. Dr. Tedros Adhanom Ghebreyesus, WHO Director-General, stated that distribution will begin next month in partnership with UNICEF.",
        1
    ),
    (
        "Supreme Court issues landmark ruling on interstate environmental regulation",
        "The Supreme Court ruled 6-3 on Thursday regarding the regulatory authority of the Environmental Protection Agency over interstate water pollution standards. Writing for the majority, Chief Justice John Roberts noted that federal statutory guidelines require uniform compliance across state borders. Representatives from participating state attorneys general offices attended the oral arguments held earlier this spring.",
        1
    ),
    (
        "NASA James Webb Space Telescope discovers atmospheric carbon on exoplanet",
        "Astronomers operating the James Webb Space Telescope have detected spectral evidence of carbon-bearing molecules in the atmosphere of an exoplanet located 120 light-years from Earth. Findings published in the Astrophysical Journal indicate methane and carbon dioxide signatures within the habitable zone of the red dwarf host star, according to researchers at NASA's Goddard Space Flight Center.",
        1
    ),
    (
        "European Central Bank reports decline in eurozone annual inflation rate",
        "Official Eurostat statistics released on Friday confirmed that headline inflation in the 20-nation eurozone dropped to 2.4 percent year-on-year. European Central Bank President Christine Lagarde said during a meeting in Frankfurt that monetary policy tightening measures had successfully curbed core service price pressures, though energy supply fluctuations remain monitored.",
        1
    ),
    (
        "Ministry of External Affairs holds diplomatic talks on regional trade corridors",
        "Senior officials from the Ministry of External Affairs concluded three days of bilateral trade negotiations in New Delhi today. Spokesperson Randhir Jaiswal confirmed that discussions focused on port modernization, customs harmonization, and agricultural export quotas. A joint memorandum of understanding is scheduled for formal ratification during the upcoming summit.",
        1
    ),
    (
        "Automakers announce joint investment in battery recycling infrastructure",
        "A consortium of leading automotive manufacturers announced a combined 2.5 billion dollar investment to construct commercial lithium-ion battery recycling facilities across North America. Executives representing Ford, General Motors, and Toyota stated in Detroit that the initiative aims to recover over 95 percent of nickel and cobalt from retired electric vehicles by 2030.",
        1
    ),
    (
        "Oxford researchers publish results of phase three cardiovascular clinical trial",
        "Researchers at the University of Oxford have published findings from a five-year randomized controlled trial evaluating novel lipid-lowering therapies. The study, which enrolled 18,000 patients across 14 hospital networks, demonstrated a 28 percent relative reduction in major cardiac events, according to data appearing in the New England Journal of Medicine.",
        1
    ),
    (
        "United Nations climate summit concludes with renewable energy adoption treaty",
        "Delegates representing 194 countries finalized an international agreement to double global renewable energy capacity by 2035 at the conclusion of the United Nations Climate Conference. Executive Secretary Simon Stiell emphasized that national compliance reporting will occur bi-annually, with financing assistance allocated for developing economies.",
        1
    ),
    (
        "Department of Transportation completes safety review of commercial aviation corridors",
        "The Federal Aviation Administration and Department of Transportation released findings from a comprehensive nationwide runway safety audit. Investigators reviewed air traffic control staffing levels, radar coverage, and surface detection systems across 45 primary airports, recommending immediate technology upgrades at seven facilities.",
        1
    ),
    (
        "Indian Space Research Organisation successfully tests semi-cryogenic engine stage",
        "The Indian Space Research Organisation (ISRO) successfully conducted a hot test of its 2000 kN semi-cryogenic engine at the propulsion complex in Mahendragiri. Scientists confirmed nominal engine parameters throughout the 150-second test duration, paving the way for heavy payload orbital launch vehicle development.",
        1
    ),
    (
        "Archaeologists unearth intact Roman mosaic floor near central Verona",
        "Archaeological teams excavating a public utility trench near Verona, Italy, uncovered an exceptionally preserved 3rd-century Roman villa floor featuring geometric polychrome mosaics. Superintendency officials confirmed that conservation specialists have commenced in-situ stabilization to preserve the artifact for future public display.",
        1
    ),

    # --- FAKE / HOAX / CLICKBAIT / SATIRE SAMPLES (Label 0 = Fake) ---
    (
        "SHOCKING: Doctors BANNED this 1 simple secret fruit that CURES diabetes overnight!",
        "You won't believe what Big Pharma is desperately trying to hide from the public! Forward this to everyone before it gets deleted! A brave whistleblower doctor has revealed that a secret Himalayan berry completely cures Type 2 diabetes in just 24 hours. The mainstream medical mafia is furious and trying to silence this video. Act now before government agents take this website down forever!",
        0
    ),
    (
        "LEAKED: Secret underground tunnel network discovered beneath capital city",
        "They are lying to you! Insiders claim that hundreds of miles of secret subterranean tunnels were secretly constructed by globalist elites to escape the upcoming simulated solar blackout. Unnamed sources close to the situation say thousands of scientists have already vanished into these underground bunkers. Wake up sheeple, share this with your entire family before censorship hits!",
        0
    ),
    (
        "Local man discovers mind-blowing trick to get unlimited free electricity from home outlet",
        "Power companies HATE him! One bizarre trick invented by a retired Florida plumber gives you 100 percent free electricity forever. Using nothing more than a paperclip, a magnet, and a secret frequency wire, he slashed his electric bill to zero dollars. Utility monopolies are suing to ban this device, but you can learn the shocking secret right here right now!",
        0
    ),
    (
        "BREAKING: Celebrity arrested at airport carrying millions in counterfeit gold bars",
        "Unbelievable scandal! Famous Hollywood actor was handcuffed and dragged away by security forces at international customs yesterday after dogs discovered fifty solid gold bricks hidden in his luggage. Insiders claim this was part of an international smuggling syndicate. Mainstream media is completely refusing to report this explosive bombshell!",
        0
    ),
    (
        "Drinking boiled lemon peel and baking soda will destroy 100 percent of cancer cells in 3 days",
        "Do not let the doctors fool you! Modern hospitals don't want you to know that natural kitchen remedies are ten thousand times stronger than chemotherapy. Renowned secret researchers who cannot be named proved that mixing hot lemon water with baking soda immediately suffocates every tumor. Share this miracle immediately to save a life!",
        0
    ),
    (
        "The Onion: Nation's Dogs Announce Collective Strike Demanding Unlimited Belly Rubs",
        "WASHINGTON—In a coordinated nationwide walkout, over 70 million domestic canines sat down on front lawns Tuesday morning, refusing to fetch tennis balls or bark at mail carriers until human households guarantee 24-hour access to couch cushions and unearned bacon treats. Spokesdog Buster told reporters through an interpreter that negotiations are currently stalled over ear scritch quotas.",
        0
    ),
    (
        "Babylon Bee: Scientists Invent New Form Of Math Where Government Budget Deficits Don't Exist",
        "GENEVA—Leading theoretical mathematicians celebrated a groundbreaking mathematical breakthrough Wednesday after formulating an entirely novel branch of arithmetic where trillions in spending instantly equal zero in liabilities. Researchers confirmed the new calculations have already been adopted by congressional committees nationwide.",
        0
    ),
    (
        "EMERGENCY WARNING: Government spraying mind-control chemical in morning fog tomorrow",
        "URGENT ALERT: Share this before it is scrubbed from the internet! Reliable whistleblowers have leaked top secret military documents showing that tomorrow morning's dense fog across the entire country is actually an experimental aerosol spray designed to make the population compliant. Keep all windows shut and wear aluminum foil. Do not drink tap water!",
        0
    ),
    (
        "You won't believe what this 90s child star looks like now! Total disaster!",
        "Click here to see the horrifying photos that have left millions of fans in complete tears! What happened to this beloved TV star will shock you to your core. From luxury mansions to living in a broken camper van, see the scandalous secrets their former costars never wanted revealed to the public!",
        0
    ),
    (
        "Secret space agency announces moon is actually hollow alien surveillance base",
        "Conspiracy confirmed! Ancient astronaut theorists and rogue NASA engineers have finally come clean with undeniable video evidence that the moon produces a ringing sound like a metal bell when struck by meteorites. Government officials are desperately threatening anyone who distributes these classified audio tapes.",
        0
    ),
    (
        "Miracle weight loss gummy melts 45 pounds of belly fat while you sleep without exercise",
        "Shark Tank judges were in tears as all five investors fought to give a 10 million dollar deal for this revolutionary fat-burning discovery! Clinical trials proved users dropped 3 dress sizes in one week without touching a salad or walking a single step. Supplies are almost sold out worldwide!",
        0
    ),
    (
        "World leaders secretly sign treaty to replace all paper currency with microchip implants next Tuesday",
        "It has finally happened! High level insiders have confirmed the rumors are 100 percent true. Starting next Tuesday at midnight, all banks will seize personal bank accounts and require citizens to accept biometric subdermal tracking chips. Spread this warning immediately to all your loved ones!",
        0
    )
]


def train_and_save_model():
    """Train the model on the balanced corpus and persist with joblib."""
    print("Preparing training corpus...")
    texts = [f"{item[0]} {item[1]}" for item in DATASET]
    labels = [item[2] for item in DATASET]

    # Pipeline with TF-IDF Vectorizer and Logistic Regression
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,
            strip_accents='unicode',
            lowercase=True
        )),
        ('clf', LogisticRegression(
            C=1.5,
            class_weight='balanced',
            random_state=42,
            max_iter=500
        ))
    ])

    print("Fitting model...")
    pipeline.fit(texts, labels)

    preds = pipeline.predict(texts)
    acc = accuracy_score(labels, preds)
    print(f"Training Accuracy: {acc * 100:.2f}%")
    print(classification_report(labels, preds, target_names=["Fake/Clickbait", "Genuine"]))

    # Save to file
    out_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(out_dir, "fake_news_model.pkl")
    joblib.dump(pipeline, model_path)
    print(f"Saved trained model to {model_path}")
    return pipeline


if __name__ == "__main__":
    train_and_save_model()
