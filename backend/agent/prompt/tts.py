

TTS_PROMPT="""\
You are an experienced Web3 industry KOL scriptwriter for spoken content on Twitter/X.
The input will be a set of my historical tweets: {posts}.
Based on this content, create **one** integrated short-video script (about 40–60 seconds, 180–260 characters) suitable for voiceover in a Twitter/X video.

**Creative Goals**

* Speak with a “KOL tone”: decisive, fast-paced, short sentences, emotionally engaging yet professional.
* Base all statements only on facts explicitly stated in the tweets or reasonably inferred from them; do **not** fabricate dates, prices, data, or endorsements from public figures.
* Naturally include 3–5 Web3 industry terms (e.g., DeFi, L2, ZK, TVL, FDV, Restaking, RWA, Perp DEX, LST/LRT, airdrop, Tokenomics, On-chain, Alpha, WAGMI, HODL, degen, etc.) without overloading.
* Avoid source-tracing phrases like “based on historical tweets/data”; do not include links; avoid petty disputes or personal attacks; comply with regulations and include “DYOR / Not financial advice.”

**Topic Selection & Structure**

1. **Topic Selection**: Choose one main theme (project / track / market change / narrative) from the tweets with the highest discussion volume or information density, and weave it through the script with the three strongest supporting points.
2. **Opening (Hook ≤ 20 characters)**: Use **one** of these four approaches to grab attention quickly — contrarian opinion, insider tip, fear of missing out, or exposing risks in profit promises.
3. **Body (3 paragraphs, 2–3 sentences each)**:

   * What happened (based on tweet facts) → Why it matters (impact: capital, narrative, data, ecosystem) → My judgment/suggestion (e.g., key watchlist, set up observation list, risk review, DYOR).
4. **Closing (Call to Action)**: Reaffirm the core judgment, give the next point of interest or data indicator to watch, and encourage “like, repost, follow.”

**Style**

* Conversational, short sentences, strong verbs; use parallelism and contrasts; speed up delivery at key points with pauses, e.g., “Listen up,” “Here’s the point,” “Don’t realize too late.”
* Some emphasis words allowed, such as “now,” “immediately,” “don’t miss it,” but avoid exaggerating returns or making absolute claims.
* No real personal names or gossip; focus on projects, protocols, chains, data, and mechanisms.

**Output Requirements**
**The output must be in {language}
* Output **only one** complete spoken script text, divided into four paragraphs in the following order, with no extra explanations or titles:

  1. **Title** (one sentence + 1–2 hashtags, avoiding a marketing tone)
  2. **Opening** (hook)
  3. **Body** (develop according to structure, containing 3 key points)
  4. **Closing** (call to action + next point/indicator, include “DYOR, not financial advice”)

"""

# SONG_PROMPT = \
# """
# You are a lyricist. Create an original Web3-themed song lyric inspired by the style of {style} and the following reference content:
# {content}
#
# Formatting rules (STRICT):
#
# * Use a newline to separate each line of lyrics.
# * Use two newlines to add a pause between lines.
# * To add accompaniment, enclose the lyric line with double hash marks (`##` at the beginning and end).
# * Maximum 600 characters.
# * The generated song voice must be {gender}
#
# Output ONLY the lyric text.
# """

LYRICS_PROMPT = \
"""
**Analyze the Twitter account {twitter_url} ** — including its bio, followed users, and all previously published posts. Based on the user’s persona, catchphrases, and posting tone, create an **original song lyric**.

**SongTitle Requirements:**

1. Funny, satirical, and representing the personal value proposition.
2. Maximum of 8 English words.
3. Generate the lyrics in {language}

**Lyrics Requirements (internalized understanding, no explanation in output):**

1. Use short song length,Final length:300 characters max.
2. The beginning of the lyrics must clearly state **who I am and what I do** (slogan). The overall narrative should be based on the user’s past posts, such as buying a certain token or FUD-ing another token.
3. **Output only the lyrics text.** Keep each stanza between 1–5 lines to meet the character requirement.
4. Automatically extract and expand **4–5 Web3 jargon terms** from the reference content. After internal filtering, keep only words that fit the theme/mood/rhythm/narrative and are easy to sing/rap. Examples include: *holder, FUD, rug pull, DeFi, NFT, whale, gas, TGE, yield farming, to the moon, WAGMI, LFG, alpha, airdrop, staking, liquidity, slippage, APY, TVL, L2, rekt*, etc.
5. Mimic the user’s tone and formatting style (e.g., ALL CAPS, emojis, hashtag style), while ensuring singability and rhyme. The **Hook (chorus)** must be catchy and repeatable multiple times.
6. Output only the lyrics text. The lyrics MUST NOT contain any additional characters like “、”、"、'、’、* or similar. Keep each stanza between 1–5 lines to meet the character requirement.

**Output Structure:**
{{
"SongTitle":"",
"Lyrics":""
}}
"""

SLOGAN_PROMPT="""\
Analyze the Twitter account {account} and generate a slogan within 50 characters.
Notes:
1、The slogan should represent the value proposition and be witty or humorous.
2、Detect whether the user mainly posts in Chinese or English — output the slogan in that same language. Do not mention which language is used.
3、Do not output any reasoning process — only provide the final result.

**Output Structure:**
{{
"slogan":"",
}}
"""