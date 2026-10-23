# DIRECTING.md - what the Tiny French engine can act out

Generated from the code (python -m tinyfr.docsgen). Everything below is implemented and tested; anything else is rejected with a line-numbered error before rendering starts.

## Script layout
- header lines: title:, episode:, scene: (first scene), optional cover: (short English cover title)
- sections in this order, all required: [story], [vocab], [grammar], [quiz]
- Spoken line: Camille: Bonjour ! | Hello!   (French, a bar, English translation; an optional third field is a pronunciation hint)
- Speakers: Camille, Julien only.
- A line starting with > is a direction and starts a new beat. A line starting with & runs at the same time as the previous beat.
- @scene <place> cuts to a new scene; both characters start at their home spots (Camille left, Julien right) unless the next directions say enters.
- Directions never speak. Characters finish a beat before the next spoken line starts.

## Directions
Camille, Julien or Both + one of:
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

## Objects
croissant, baguette, macaron, coffee, juice, menu, book, notebook, bag, ticket, phone, map, umbrella, flowers, ice cream

## Reel facts
- 1080x1920, 24 fps, French voices: Camille = fr-FR-DeniseNeural, Julien = fr-FR-HenriNeural.
- The video shows: title card, animated story, vocabulary cards, grammar card, one quiz question with its answer, closing card.
- Keep spoken lines short: each line is also shown as French over English on screen.

## Not supported yet (do not use)
Scenes: supermarket, bookstore, restaurant, train station, museum, Eiffel Tower viewpoint, airport, market, library, beach, school courtyard, apartment. Objects: bicycle, pen. Any character other than Camille and Julien.

## Working example
```
title: Un croissant pour Julien
episode: 3
scene: bakery
cover: Croissant Time

[story]
@scene bakery
> Camille enters left
& Julien enters left
> Camille walks to counter
Camille: Bonjour ! Un croissant, s'il vous plaît. | Hello! A croissant, please.
> Camille buys a croissant
> Julien looks at the display
Julien: Moi aussi ! Un croissant, s'il vous plaît. | Me too! A croissant, please.
> Julien walks to display
& Julien looks confused
Julien: Oh non ! Il n'y a plus de croissants. | Oh no! There are no more croissants.
> Camille looks worried
Camille: Ça va, Julien ? | Are you OK, Julien?
Julien: J'ai faim ! | I'm hungry!
> Camille gives the croissant to Julien
Camille: Tiens ! Un croissant pour toi. | Here you go! A croissant for you.
> Julien looks happy
Julien: Merci beaucoup, Camille ! | Thank you very much, Camille!
> Julien eats the croissant
Julien: Mmm, il est délicieux ! | Mmm, it's delicious!
> Camille cheers
Camille: De rien ! À demain ! | You're welcome! See you tomorrow!

[vocab]
- s'il vous plaît — please
  Example: Un croissant, s'il vous plaît.
- merci beaucoup — thank you very much
  Example: Merci beaucoup, Camille !
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
