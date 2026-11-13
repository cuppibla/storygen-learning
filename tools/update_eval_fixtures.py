#!/usr/bin/env python3
"""Regenerate curated six-scene golden responses; validate before writing."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared/backend"))
from story_contract import EXAMPLE_STORY, SCENE_BEATS, parse_story_response


def make(characters, rows):
    scenes = [dict(index=i + 1, beat=beat, title=title, description=description,
                   characters=list(characters), text=text)
              for i, (beat, (title, description, text)) in enumerate(zip(SCENE_BEATS, rows))]
    return parse_story_response(json.dumps(dict(
        schema_version=2, story="\n\n".join(s["text"] for s in scenes),
        main_characters=[dict(name=name, description=desc) for name, desc in characters.items()], scenes=scenes)))


STORIES = {
    "brave knight, enchanted castle, magical sword": make(
        {"Aria": "A young knight with a chestnut braid, hazel eyes, silver armor, a teal cloak, brown boots and a round wooden shield painted with a golden leaf."}, [
        ("The Castle Bell", "Aria approaching an enchanted castle above a misty village.", "Aria was a brave knight who mended things rather than broke them. When the enchanted castle stopped singing, shadows crept toward the village. She packed her wooden shield and followed the silent road uphill."),
        ("A Door Without Light", "Aria facing a closed castle door beside an unlit lantern.", "At the gate, a carved riddle asked for something bright that could not burn. Aria noticed an empty lantern. Beyond the door, a magical sword waited, but the castle would not welcome anyone who hurried."),
        ("The First Bright Answer", "Aria guiding sunlight into the lantern with her polished shield.", "She tried catching sunlight in her polished shield and guiding it into the lantern. A warm beam danced across the glass. Aria smiled, but the heavy door remained closed, waiting for a kinder answer than cleverness alone."),
        ("Clouds Over the Courtyard", "Aria sheltering as clouds hide the sun and the beam fades.", "Then clouds covered the sun, and her beam faded. Aria felt discouraged, but remembered the village children sharing lanterns on dark evenings. Perhaps the castle needed light that came from caring, not showing off."),
        ("A Light Worth Sharing", "Aria offering a firefly shelter inside the lantern as the door opens.", "A firefly rested beneath a leaf. Aria gently opened her lantern and offered shelter. The firefly glowed inside, and the castle doors swung wide. The magical sword shone nearby, recognizing her patient and generous heart."),
        ("The Song Returns", "Aria carrying the glowing sword toward the village as shadows retreat.", "Aria carried the sword home, using its gentle light to guide neighbors through the shadows. The castle began singing again. Everyone called her brave, but Aria knew the smallest kindness had opened the biggest door.")]),
    "wise owl, ancient library, secret knowledge": make(
        {"Hoot": "A wise brown owl with cream-speckled feathers, round amber eyes, tiny gold spectacles and a blue satchel.", "Mina": "A young scholar with dark curly hair, green eyes, a mustard-yellow coat and a notebook tied with red string."}, [
        ("The Quiet Shelves", "Hoot arranging books while Mina enters the ancient library.", "Hoot was a wise owl who cared for an ancient library. One evening, Mina arrived seeking secret knowledge to help her grandmother sleep. Hoot offered tea, opened his notebook, and promised they would search together."),
        ("A Missing Recipe", "Hoot and Mina examining an empty recipe stand beneath a painted moon.", "The index pointed to a moonlit recipe, but its stand was empty. Mina worried they had come too late. Hoot studied the dusty floor and found a trail of silver letters leading toward the tallest shelf."),
        ("Following the Letters", "Mina climbing a rolling ladder while Hoot steadies it.", "Mina climbed the rolling ladder while Hoot held it steady. They followed the letters to a book wrapped in blue cloth. Inside, a recipe described a soothing drink, yet one important line was hidden beneath a fold."),
        ("The Torn Corner", "Hoot and Mina studying a torn page while rain taps the windows.", "A torn corner concealed the final instruction. Mina sighed, and Hoot nearly guessed the missing words. Instead, he closed the book. A good helper checks carefully, he explained, especially when someone dear is waiting at home."),
        ("Reading by Moonlight", "Hoot holding the page toward moonlight while Mina reads the reverse.", "Moonlight slipped through the window and revealed faint writing on the reverse. Together they read the missing instruction: stir slowly while remembering a happy moment. Mina copied it carefully, and Hoot packed the book for her."),
        ("Knowledge for Everyone", "Mina sharing a copied recipe and a warm cup with Hoot.", "Mina hurried home with the recipe and returned the next morning smiling. Her grandmother had slept peacefully. She gave Hoot a copy for the library, where secret knowledge became a gift that everyone could share.")]),
    "space explorer, alien planet, friendly aliens": make(
        {"Nova": "A space explorer with brown skin, short black curls, a white spacesuit with orange patches, purple boots and a clear helmet."}, [
        ("A New Blue World", "Nova stepping from a silver rocket onto a blue alien planet.", "Nova was a space explorer visiting a blue alien planet. She collected pictures, not rocks, so discoveries could stay beautiful for everyone. Her orange patches stood out against the curling silver plants near the rocket."),
        ("A Puzzling Beep", "Nova listening to friendly aliens beside a broken windmill.", "Three friendly aliens waved beside a silent windmill. Their leader offered Nova a map covered in musical notes. A puzzling beep came from the machine, and Nova realized the visitors were asking for help, not hiding treasure."),
        ("Turning the Map", "Nova rotating the map while an alien points to a loose wheel.", "Nova turned the map upside down and matched its notes to the windmill wheels. She tightened the loosest wheel while the aliens watched. A soft hum began, but the sails still refused to turn in the breeze."),
        ("A Tangled Sail", "Nova untangling a silver vine as dust swirls around her boots.", "Dust swirled around her boots, and a silver vine caught in the sail. Nova pulled too quickly, making the knot tighter. She sat down and took a breath. Exploring a new world meant learning its rules first."),
        ("The Windmill Song", "Nova and the aliens guiding the vine aside while the sails turn.", "Nova noticed the vine bent toward music. She hummed the map’s gentlest note, and the aliens joined in. The vine relaxed, the sail slipped free, and the windmill spun, sending warm light across their blue world."),
        ("A Sky Full of Friends", "Nova picnicking beneath the glowing windmill with friendly aliens.", "The friendly aliens invited Nova to picnic beneath the glowing sails. She added their song to her discoveries. As her rocket lifted toward the stars, Nova waved, knowing every new world held friends to understand.")]),
    "tree": make(
        {"Willow": "A young willow tree with a smooth gray-brown trunk, trailing branches, narrow green leaves and a heart-shaped hollow."}, [
        ("The Courtyard Tree", "Willow trailing branches over a courtyard and stone bench.", "Willow was a young tree in a busy courtyard. Her long branches brushed the stones, and children rested beneath her leaves. She wished she could do something useful instead of simply standing in the same place."),
        ("A Tumbled Nest", "Willow noticing a fallen nest beside her roots after a gust.", "One windy morning, a tiny nest tumbled beside her roots. Two sparrows circled above it, chirping anxiously. Willow could not walk or lift her branches high, but she could bend them low enough to help."),
        ("A Leafy Cradle", "Willow bending a low branch into a cradle around the nest.", "She lowered her softest branch and curled its leaves into a cradle. The sparrows nudged their nest inside. Willow held it carefully, feeling proud as the little family settled among the green leaves above the bench."),
        ("Rain in the Leaves", "Willow sheltering the nest as rain drips through thin lower branches.", "Then rain began to fall. Her lower leaves were too thin to keep the nest dry, and water dripped through. Willow worried she had promised more than she could give. The sparrows huddled close beneath her bending branch."),
        ("Room in the Hollow", "Willow guiding the sparrows and nest into her heart-shaped hollow.", "Willow remembered the little hollow in her trunk. She bent the cradle closer and closer until the sparrows could hop inside. The nest fitted perfectly, protected from the rain by sturdy wood and a curtain of leaves."),
        ("A Useful Kind of Stillness", "Willow sheltering sleeping sparrows while children sit beneath her branches.", "By morning, the sparrows were singing. Children gathered beneath Willow’s branches, listening to the new song. Willow stood in her usual place, but it no longer felt ordinary. Being steady had given someone a home.")]),
    "friendly dragon, magical forest, lost treasure": make(
        {"Ember": "A friendly dragon with emerald scales, amber eyes, rounded wings, a cream belly, four short legs and a tail with soft green spikes."}, [
        ("The Forest Guardian", "Ember watering seedlings among glowing mushrooms in a magical forest.", "Ember was a friendly dragon who tended a magical forest. She watered seedlings and listened to the mushrooms’ stories. One morning, an old map appeared beneath her favorite stone, marking lost treasure beyond the winding silver stream."),
        ("The Map’s Promise", "Ember studying the treasure map beside a glowing mushroom.", "The map promised something precious enough to help the whole forest. Ember packed a basket of berries and followed its dotted path. Every glowing mushroom seemed to lean closer, curious about where the adventure would lead."),
        ("Across the Stepping Stones", "Ember crossing stepping stones over a silver stream with a berry basket.", "Ember tried crossing the silver stream on stepping stones. She moved slowly, balancing her basket and tail. Halfway across, she heard a tiny cry. A turtle was trapped beneath a branch near the rushing water."),
        ("The Missing Stone", "Ember reaching toward the turtle as a stepping stone slips underwater.", "The last stone slipped underwater, and Ember could not reach the turtle safely. Her map floated away, but she let it go. Treasure could wait. She needed a better way to help without sweeping them both downstream."),
        ("A Bridge of Kindness", "Ember laying a fallen log across the stream for the turtle.", "Ember spotted a fallen log and gently laid it across the stream. The turtle climbed to safety, then showed her a shallow path. At its end, Ember found a healing crystal, the forest’s lost treasure."),
        ("The Greatest Treasure", "Ember healing a wounded mushroom with the crystal while the turtle watches.", "Back home, Ember used the crystal to heal a wounded mushroom. The turtle visited often, and the map dried beside the fire. Ember smiled at her sparkling forest, knowing kindness had guided her better than any dotted line.")]),
    "butterfly, garden": make(
        {"Luna": "A small butterfly with violet wings edged in turquoise, black vein patterns, a fuzzy dark body, two curved antennae and six delicate legs."}, [
        ("Morning in the Garden", "Luna resting on a yellow flower beside a wooden garden fence.", "Luna was a butterfly who knew every corner of a colorful garden. She visited the daisies each morning and rested beside the fence at noon. Her violet wings made the children smile whenever she fluttered past."),
        ("Flowers Facing Down", "Luna hovering above drooping flowers and an empty watering can.", "One hot morning, the flowers drooped and bees gathered around an empty watering can. Luna wondered why the gardener had not visited. She followed the path to the gate and found it stuck against a stone."),
        ("A Wing-Sized Push", "Luna pushing a small pebble beside the gate while bees watch.", "Luna tried moving the pebble with all her weight. It did not budge. Then she pushed a smaller seed, hoping to make a path for water. The seed rolled away, but the garden stayed thirsty."),
        ("The Hot Wind", "Luna sheltering beneath a broad leaf as hot wind bends flowers.", "A hot wind bent the flowers, and Luna sheltered beneath a leaf. She felt too small to help. Then she noticed children watching from the other side of the gate, waiting for someone to show them trouble."),
        ("A Fluttering Invitation", "Luna fluttering above the gate while children move the pebble.", "Luna flew above the gate, then dipped toward the pebble again and again. The children followed her, moved the stone, and opened the path. They carried watering cans between the rows while Luna guided them to the driest flowers."),
        ("The Garden Dances", "Luna flying over revived flowers as children and bees share the garden.", "By evening, the garden lifted its bright faces. Bees hummed, children laughed, and Luna danced above the daisies. She had not moved the stone herself, but her tiny wings had shown everyone where help was needed.")]),
    "tiny robot, rainy city, lost kitten": EXAMPLE_STORY,
}


def main():
    folder = ROOT / "03b_Agent_Evaluation_Done/backend/story_agent"
    count = 0
    for path in folder.glob("*.json"):
        data = json.loads(path.read_text())
        for case in data.get("eval_cases", []):
            for turn in case["conversation"]:
                keywords = turn["user_content"]["parts"][0]["text"].removeprefix("Keywords: ")
                turn["final_response"]["parts"][0]["text"] = json.dumps(STORIES[keywords], ensure_ascii=False, indent=2)
                count += 1
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    config = folder / "test_config.json"
    data = json.loads(config.read_text())
    data["custom_evaluators"]["json_structure_validator"].update(
        required_fields=["schema_version", "story", "main_characters", "scenes"], scene_count=6,
        scene_fields=["index", "beat", "title", "description", "characters", "text"], scene_beats=list(SCENE_BEATS))
    data["custom_evaluators"]["story_quality_metrics"].update(min_word_count=180, max_word_count=270)
    data["evaluation_notes"]["story_agent_specifics"] = [
        "Schema version 2; valid JSON with exactly six scenes indexed 1–6",
        "Beats: setup, inciting_incident, first_attempt, setback, climax, resolution",
        "Each scene text is 25–50 words; total story is 180–270 words",
        "Only declared main characters appear in scene.characters",
        "The story equals the six scene texts joined in order",
        "Golden responses are regression fixtures, not proof of live model quality"]
    config.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Validated and updated {count} golden story responses.")


if __name__ == "__main__":
    main()
