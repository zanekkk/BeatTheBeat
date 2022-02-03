define e = Character("BeatTheBeat")
image gameBackground = "gamebackground.png"
image studioBackground = "game_menu.png"

label start:

    show studioBackground
    e "Let's beat the beat! You have to press the arrows on your keyboard according to the rhythm."
    $ quick_menu = False

    # unikanie cofnięcia się i utraty stanu gry
    $ renpy.block_rollback()

    show gameBackground
    call screen beatTheBeat(
         'audio/musicNewShort.mp3',
         'audio/musicNewShort.beatmap.txt')

    # unikanie cofnięcia się i wejscia do gry od nowa
    $ renpy.block_rollback()

    $ renpy.checkpoint()

    $ quick_menu = True
    window show

    $ num_hits, num_notes = _return
    e "You hit [num_hits] notes out of [num_notes]. Good work!"

    return