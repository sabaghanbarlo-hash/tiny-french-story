# DIRECTING.md - what the Tiny French engine can act out

Generated from the code (python -m tinyfr.docsgen). Everything below is implemented and tested; anything else is rejected with a line-numbered error before rendering starts.

## Script layout
- header lines: title:, episode:, scene: (first scene, or `auto` to pick the place from the story), optional cover: (short English cover title)
- sections in this order, all required: [story], [vocab], [grammar], [quiz]
- Spoken line: Marinette: Bonjour ! | Hello!   (French, a bar, English translation; an optional third field is a pronunciation hint)
- Speakers: Marinette, Adrien only.
- A line starting with > is a direction and starts a new beat. A line starting with & runs at the same time as the previous beat.
- @scene <place> cuts to a new scene; both characters start at their home spots (Marinette left, Adrien right) unless the next directions say enters.
- Directions never speak. Characters finish a beat before the next spoken line starts.

## Directions
Marinette, Adrien or Both + one of:
- enters left|right [to <spot>]
- exits left|right
- walks to <spot>
- runs to <spot>
- looks <feeling>
- looks at <name>
- faces <name|left|right>
- waves
- jumps
- laughs
- nods
- cheers
- holds <item>
- picks up <item>
- buys <item>
- eats [item]
- drinks [item]
- drops|puts away|finishes [item]
- gives <item> to <name>
- wait <seconds>

Base verbs also work with Both (Both walk to counter). Targets for walks to / enters ... to: a scene spot, left, center, right, home, next to <name>, or a percentage such as 40%.
- A character whose first direction in a scene is enters starts off screen; otherwise they are already standing at home.
- Walking to a spot keeps at least a body width between the two characters; if they must pass each other, one walks behind the other.
- gives needs the giver to hold the item and the receiver to have empty hands; the giver walks over first if too far away.
- eats works on: baguette, croissant, ice cream, macaron. drinks works on: coffee, juice. Eaten food disappears; a cup stays until puts away.
- A character can hold one item at a time.

## Feelings (looks <feeling>)
confused, embarrassed, excited, happy, neutral, sad, shy, surprised, worried (also accepted: glad, smiling, puzzled, shocked, nervous, thrilled)

## Scenes
| Scene (@scene / scene:) | Also accepted | Named spots |
|---|---|---|
| street | paris street, road, city | lamp, bench, shop window |
| bakery | boulangerie, pastry shop | entrance, window, counter, display |
| cafe | café, coffee shop | entrance, table, counter |
| park | garden, jardin | bench, fountain |
| classroom | school, class | door, board, desk |
| metro | metro station, subway, métro | entrance, ticket machine, platform |
| supermarket | supermarché, grocery, grocery store, store | entrance, fruit stand, shelves, checkout |
| bookstore | librairie, book store, bookshop | entrance, shelves, reading corner, counter |
| restaurant | resto, dining room | entrance, table, window table, counter |
| train station | gare, station, railway station, train | entrance, ticket window, departures board, platform |
| museum | musée, gallery, art museum | entrance, painting, statue, bench |
| eiffel | eiffel tower, tour eiffel, trocadéro, viewpoint, eiffel viewpoint | steps, viewpoint, bench |

## Objects
croissant, baguette, macaron, coffee, juice, menu, book, notebook, bag, ticket, phone, map, umbrella, flowers, ice cream

## Reel facts
- 1080x1920, 24 fps, French voices: Marinette = fr-FR-DeniseNeural, Adrien = fr-FR-HenriNeural.
- The video shows: title card, animated story, vocabulary cards, grammar card, one quiz question with its answer, closing card.
- Keep spoken lines short: each line is also shown as French over English on screen.

## Not supported yet (do not use)
Scenes: supermarket, bookstore, restaurant, train station, museum, Eiffel Tower viewpoint, airport, market, library, beach, school courtyard, apartment. Objects: bicycle, pen. Any character other than Marinette and Adrien.

## Working example
```
title: Un croissant pour Adrien
episode: 3
scene: bakery
cover: Croissant Time

[story]
@scene bakery
> Marinette enters left
& Adrien enters left
> Marinette walks to counter
Marinette: Bonjour ! Un croissant, s'il vous plaît. | Hello! A croissant, please.
> Marinette buys a croissant
> Adrien looks at the display
Adrien: Moi aussi ! Un croissant, s'il vous plaît. | Me too! A croissant, please.
> Adrien walks to display
& Adrien looks confused
Adrien: Oh non ! Il n'y a plus de croissants. | Oh no! There are no more croissants.
> Marinette looks worried
Marinette: Ça va, Adrien ? | Are you OK, Adrien?
Adrien: J'ai faim ! | I'm hungry!
> Marinette gives the croissant to Adrien
Marinette: Tiens ! Un croissant pour toi. | Here you go! A croissant for you.
> Adrien looks happy
Adrien: Merci beaucoup, Marinette ! | Thank you very much, Marinette!
> Adrien eats the croissant
Adrien: Mmm, il est délicieux ! | Mmm, it's delicious!
> Marinette cheers
Marinette: De rien ! À demain ! | You're welcome! See you tomorrow!

[vocab]
- s'il vous plaît — please
  Example: Un croissant, s'il vous plaît.
- merci beaucoup — thank you very much
  Example: Merci beaucoup, Marinette !
- tiens — here you go
  Example: Tiens ! Un croissant pour toi.
- délicieux — delicious
  Example: Il est délicieux !

[grammar]
- Il n'y a plus de + noun — There is no more...
  Example 1: Il n'y a plus de croissants.
  Example 2: Il n'y a plus de café.

[quiz]
Q: What does "Il n'y a plus de croissants" mean?
A) There are no more croissants.
B) There are many croissants.
C) I want a croissant.
Answer: A
Explanation: "Il n'y a plus de" means "there is no more" - the shop has run out.
```
