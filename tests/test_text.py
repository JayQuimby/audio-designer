from voice_assist.text import clean_for_speech, paragraphs, pop_sentences


def test_waits_for_sentence_end():
    assert pop_sentences("Hello there, this is the start of a long")[0] == []


def test_splits_finished_sentences_and_keeps_remainder():
    done, rest = pop_sentences("The capital of France is Paris. It sits on the river Seine. And it", min_len=20)
    assert done == ["The capital of France is Paris.", "It sits on the river Seine."]
    assert rest == "And it"


def test_short_sentences_merge():
    done, rest = pop_sentences("Yes. Sure. That works for me, thanks. Next", min_len=20)
    assert done == ["Yes. Sure. That works for me, thanks."]
    assert rest == "Next"


def test_decimals_do_not_split():
    done, rest = pop_sentences("Pi is about 3.14159 and e is 2.718 roughly.")
    assert done == [] and rest.endswith("roughly.")


def test_streaming_piecewise_loses_nothing():
    text = "One sentence is here for you. Another sentence follows right after it. Last bit"
    buf, spoken = "", []
    for ch in text:
        buf += ch
        done, buf = pop_sentences(buf)
        spoken += done
    assert " ".join(spoken + [buf]) == text


def test_clean_and_paragraphs():
    assert clean_for_speech("**Bold** and `code` # head") == "Bold and code  head"
    assert paragraphs("a\n\n  b  \n") == ["a", "b"]
