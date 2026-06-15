var root = document.body

var LANGUAGE_OPTIONS = [
    ["af-ZA", "Afrikaans"],
    ["ar-XA", "Arabic"],
    ["bn-IN", "Bengali"],
    ["bg-BG", "Bulgarian"],
    ["ca-ES", "Catalan"],
    ["yue-HK", "Chinese (Hong Kong)"],
    ["cs-CZ", "Czech"],
    ["da-DK", "Danish"],
    ["nl-BE", "Dutch (Belgium)"],
    ["nl-NL", "Dutch (Netherlands)"],
    ["en-AU", "English (Australia)"],
    ["en-IN", "English (India)"],
    ["en-GB", "English (UK)"],
    ["en-US", "English (US)"],
    ["fil-PH", "Filipino"],
    ["fi-FI", "Finnish"],
    ["fr-CA", "French (Canada)"],
    ["fr-FR", "French (France)"],
    ["de-DE", "German"],
    ["el-GR", "Greek"],
    ["gu-IN", "Gujarati"],
    ["hi-IN", "Hindi"],
    ["hu-HU", "Hungarian"],
    ["is-IS", "Icelandic"],
    ["id-ID", "Indonesian"],
    ["it-IT", "Italian"],
    ["ja-JP", "Japanese"],
    ["kn-IN", "Kannada"],
    ["ko-KR", "Korean"],
    ["lv-LV", "Latvian"],
    ["ms-MY", "Malay"],
    ["ml-IN", "Malayalam"],
    ["cmn-CN", "Mandarin Chinese"],
    ["mr-IN", "Marathi"],
    ["nb-NO", "Norwegian"],
    ["pl-PL", "Polish"],
    ["pt-BR", "Portuguese (Brazil)"],
    ["pt-PT", "Portuguese (Portugal)"],
    ["pa-IN", "Punjabi"],
    ["ro-RO", "Romanian"],
    ["ru-RU", "Russian"],
    ["sr-RS", "Serbian"],
    ["sk-SK", "Slovak"],
    ["es-ES", "Spanish (Spain)"],
    ["es-US", "Spanish (US)"],
    ["sv-SE", "Swedish"],
    ["ta-IN", "Tamil"],
    ["te-IN", "Telugu"],
    ["th-TH", "Thai"],
    ["tr-TR", "Turkish"],
    ["uk-UA", "Ukrainian"],
    ["vi-VN", "Vietnamese"],
]

function renderLanguageSelect(id, value, onChange) {
    return m("select#" + id, { onchange: onChange, value: value },
        LANGUAGE_OPTIONS.map(function (option) {
            return m("option[value=" + option[0] + "]", option[1])
        }))
}

function renderCopyControls() {
    return [
        m("small", "Insert in Estuary terminal: "),
        m("pre", State.lastreslist()),
        m("img", { onclick: function () { State.copyreslist() }, src: "assets/clipboard.png", height: "16" }),
        State.copied ? m("span.copied", "copied") : null,
        m("br"),
        m("br"),
        m("small", "Insert in Strudel: "),
        m("pre", State.lastreslist(true)),
        m("img", { onclick: function () { State.copyreslist(true) }, src: "assets/clipboard.png", height: "16" }),
        State.strudelcopied ? m("span.copied", "copied") : null,
    ]
}

function renderPhonemeSentence(sentence) {
    return m("div.phoneme-sentence", sentence.map(function (word) {
        return m("div.phoneme-word", [
            m("strong", word.word),
            word.ipa ? m("span.phoneme-ipa", word.ipa) : null,
            word.arpabet ? m("span.phoneme-arpabet", word.arpabet) : null,
            word.stress_pattern ? m("span.phoneme-stress", word.stress_pattern) : null,
        ])
    }))
}

function renderPhonemeBank(bank, urls) {
    return m("div.phoneme-bank", [
        m("h4", bank),
        m("ul.samples", urls.map(function (url) {
            return m("li", m("audio", { controls: true, src: url }))
        }))
    ])
}

function flattenStringLists(nestedLists) {
    var flat = []
    ;(nestedLists || []).forEach(function (list) {
        ;(list || []).forEach(function (item) {
            flat.push(String(item))
        })
    })
    return flat
}

function toQuotedStringList(lines) {
    if (!lines || lines.length === 0) {
        return "[]"
    }
    return "[\n" + lines.map(function (line) {
        return "  \"" + String(line).replace(/\\/g, "\\\\").replace(/\"/g, "\\\"") + "\","
    }).join("\n") + "\n]"
}

function normalizePhonemeDefinition(definition) {
    return definition.trim()
        .replace(/\r?\n+/g, ",")
        .replace(/\s*,\s*/g, ",")
        .replace(/[ \t]+/g, "_")
    .toLowerCase()
    .replace(/[^a-z0-9_,]+/g, "")
    .replace(/_+/g, "_")
        .replace(/,+/g, ",")
        .replace(/^,|,$/g, "")
}

var State = {
    pack: "",
    progress: false,
    lastretrievedtype: "",
    lastretrieved: "",
    lastreslistcontents: [],
    error: "",
    licenses: ["by", "cc0", "by-nc"],
    speech: "",
    speechLanguage: "uk-UA",
    speechGender: "f",
    phonemes: "",//Papa was a rolling stone\n(Wherever he laid his hat)\n(was his home)\n(And when he died)\n(All he left us was alone)\nSay Papa\nBuild Papa up\nScream Papa",
    phonemeLanguage: "en-GB",
    phonemeGender: "m",
    phonemeOverrides: "", //"papa:P_AA1_P_A",
    beatsPerBar: 4,
    barsPerLine: 2,
    targetStressBeat: 3,
    tab: "pack",
    phonemePreview: true,
    freesoundAvailable: true,
    freesoundError: null,
    freesoundErrorReason: null,

    pollStatus: function () {
        m.request({ method: "GET", url: "/status" })
            .then(function (result) {
                State.freesoundAvailable = result.freesound.available
                State.freesoundError = result.freesound.error
                State.freesoundErrorReason = result.freesound.reason
            })
            .catch(function () {
                // If /status itself fails, leave the current state unchanged
            })
    },

    licensefullname: function (name) {
        switch (name) {
            case "cc0": return "Public domain"
            case "by": return "Attribution"
            case "by-nc": return "Attribution non-commercial"
        }
    },

    haslicense: function (name) {
        return State.licenses.includes(name)
    },

    setlicense: function (e) {
        var name = e.target.value
        if (State.licenses.includes(name)) {
            State.licenses = State.licenses.filter(function (value) {
                return value != name
            })
        }
        else {
            State.licenses.push(name)
        }
    },

    lastretrievedreslist: function () {
        return this.lastretrieved + ".json"
    },

    lastretrievedzip: function () {
        return window.location + this.lastretrieved + ".zip"
    },

    lastreslist: function (strudel = false) {
        var url = new URL(location.href + State.lastretrievedreslist())
        if (this.lastretrievedtype == "pack" && State.licenses.length < 3) {
            url.searchParams.append("licenses", State.licenses.join())
        }
        if (this.lastretrievedtype == "speech") {
            url.searchParams.append("gender", State.speechGender)
            url.searchParams.append("language", State.speechLanguage)
        }
        if (this.lastretrievedtype == "phonemes") {
            url.searchParams.append("gender", State.phonemeGender)
            url.searchParams.append("language", State.phonemeLanguage)
            if (State.phonemeOverrides.trim()) {
                url.searchParams.append("overrides", State.phonemeOverrides.trim())
            }
        }
        if (this.lastretrievedtype == "phonemes") {
            url.searchParams.append("beats_per_bar", State.beatsPerBar)
            url.searchParams.append("bars_per_line", State.barsPerLine)
            url.searchParams.append("target_stress_beat", State.targetStressBeat)
        }
        if (strudel) {
            url.searchParams.append("strudel", 1)
            return "samples('" + url.href + "')"
        }
        return '!reslist "' + url.href + '"'
    },

    retrieve: function () {
        if (!State.pack) {
            State.error = "Please enter a pack definition"
            return
        }

        State.error = ""
        State.progress = true
        m.request({
            method: "GET",
            url: "/pack/" + encodeURIComponent(State.pack) + "?licenses=" + State.licenses.join(),
        })
            .then(function (result) {
                State.progress = false
                if (result.status == "ok") {
                    State.lastretrieved = result.definition
                    State.lastretrievedtype = "pack"
                    m.request({
                        method: "GET",
                        url: encodeURIComponent(State.lastretrievedreslist()) + "?complete=1&licenses=" + State.licenses.join(),
                    }).then(function (result) {
                        State.lastreslistcontents = result
                    })
                }
                else if (result.status == "empty") {
                    State.error = "Pack is empty"
                }
                else {
                    State.error = "An error occured"
                }
            })
            .catch(function (error) {
                State.progress = false
                if (error.code === 503 && error.response && error.response.status === "freesound_unavailable") {
                    State.error = "Freesound is currently unavailable. Try again later."
                    State.freesoundAvailable = false
                    State.freesoundError = error.response.error
                }
                else {
                    State.error = "An error occured"
                }
            })
    },

    copyreslist: function (strudel = false) {
        if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
            if (navigator.clipboard.writeText(State.lastreslist(strudel))) {
                if (strudel) {
                    State.strudelcopied = true
                }
                else {
                    State.copied = true
                }
            }
        }
        if (strudel) {
            setTimeout(function () {
                State.strudelcopied = false
                m.redraw()
            }, 2000)
        }
        else {
            setTimeout(function () {
                State.copied = false
                m.redraw()
            }, 2000)
        }
    },

    retrievespeech: function () {
        if (!State.speech) {
            State.error = "Please enter a pack definition"
            return
        }

        State.error = ""
        State.progress = true
        m.request({
            method: "GET",
            url: "/speech/" + encodeURIComponent(State.speech) + "?language=" + State.speechLanguage + "&gender=" + State.speechGender,
        })
            .then(function (result) {
                State.progress = false
                if (result.status == "ok") {
                    State.lastretrieved = "speech/" + result.definition
                    State.lastretrievedtype = "speech"
                    m.request({
                        method: "GET",
                        url: encodeURIComponent(State.lastretrievedreslist()) + "?language=" + State.speechLanguage + "&gender=" + State.speechGender,
                    }).then(function (result) {
                        State.lastreslistcontents = result
                    })
                }
                else if (result.status == "empty") {
                    State.error = "Pack is empty"
                }
                else {
                    State.error = "An error occured"
                }
            })
            .catch(function () {
                State.progress = false
                State.error = "An error occured"
            })
    },

    retrievephonemes: function (preview = true) {
        if (!State.phonemes) {
            State.error = "Please enter a phoneme definition"
            return
        }

        State.error = ""
        State.progress = true
        State.phonemePreview = preview
        var phonemeDefinition = normalizePhonemeDefinition(State.phonemes)
        var phonemeOverrides = State.phonemeOverrides.trim()
        var query =
            "?language=" + State.phonemeLanguage +
            "&gender=" + State.phonemeGender +
            "&beats_per_bar=" + State.beatsPerBar +
            "&bars_per_line=" + State.barsPerLine +
            "&target_stress_beat=" + State.targetStressBeat +
            "&strudel=1&details=1&preview=" + (preview ? 1 : 0)
        if (phonemeOverrides) {
            query += "&overrides=" + encodeURIComponent(phonemeOverrides)
        }
        m.request({
            method: "GET",
            url: "/phonemes/" + encodeURIComponent(phonemeDefinition) + ".json" + query,
        })
            .then(function (result) {
                State.progress = false
                if (result._base) {
                    State.lastretrieved = "phonemes/" + phonemeDefinition
                    State.lastretrievedtype = "phonemes"
                    State.lastreslistcontents = result
                }
                else {
                    State.error = "An error occured"
                }
            })
            .catch(function () {
                State.progress = false
                State.error = "An error occured"
            })
    },
}

var Shabda = {
    view: function () {
        var phonemeBanks = Object.keys(State.lastreslistcontents || {}).filter(function (key) {
            if (key.charAt(0) == "_") {
                return false
            }
            if (
                key == "sentences_strudel" ||
                key == "sentences_strudel_timed" ||
                key == "sentences_phonetic" ||
                key == "beats_per_bar" ||
                key == "bars_per_line"
            ) {
                return false
            }
            return Array.isArray(State.lastreslistcontents[key])
        })

        return m("main", [
            !State.freesoundAvailable ? m("div#freesound-banner",
                State.freesoundErrorReason === "auth"
                    ? [
                        "⚠ Freesound authorization has expired. New sample fetching is disabled. ",
                        m("strong", "Existing samples and speech generation remain available."),
                    ]
                    : [
                        "⚠ Freesound is currently unreachable. New sample fetching is disabled. ",
                        m("strong", "Existing samples and speech generation remain available."),
                    ]
            ) : null,

            m("h1", [m("img", { src: "assets/logo.svg", height: "40", title: 'Shabda is the Sanskrit word for "speech sound"' }), "Shabda"]),

            m("p.intro", [
                "Shabda is a tool for assembling and sharing packs of found audio samples.",
                m("br"),
                "It fetches samples from ",
                m("a", { href: "https://freesound.org/" }, "freesound.org"),
                " based on given words or generates Text-to-Speech samples, for use in impro sessions on instruments such as ",
                m("a", { href: "https://tidalcycles.org/" }, "Tidal Cycles"),
                ", ",
                m("a", { href: "https://estuary.mcmaster.ca/" }, "Estuary"),
                " and ",
                m("a", { href: "https://strudel.tidalcycles.org/" }, "Strudel"),
                ".",
            ]),

            m("div", [
                m("div#tabs", [
                    m("span#packs_tab", {
                        class: State.tab == "pack" ? "selected" : "",
                        onclick: function () { State.tab = "pack" },
                    }, "Pack"),
                    m("span#speech_tab", {
                        class: State.tab == "speech" ? "selected" : "",
                        onclick: function () { State.tab = "speech" },
                    }, "Speech"),
                    m("span#phonemes_tab", {
                        class: State.tab == "phonemes" ? "selected" : "",
                        onclick: function () { State.tab = "phonemes" },
                    }, "Phonemes"),
                ]),

                m("div.tabcontent", { style: State.tab == "pack" ? "display:block;" : "" }, [
                    m("input[placeholder=Pack definition]#definition", {
                        value: State.pack,
                        oninput: function (e) { State.pack = e.target.value },
                        onkeyup: function (e) {
                            if (e.keyCode == 13) {
                                State.retrieve()
                            }
                        },
                    }),
                    m("div#licenses", [
                        m("input[type=checkbox]#license-cc0", { name: "licenses", value: "cc0", checked: State.haslicense("cc0"), oninput: State.setlicense }),
                        m("label[for=license-cc0]", State.licensefullname("cc0")),
                        m("br"),
                        m("input[type=checkbox]#license-by", { name: "licenses", value: "by", checked: State.haslicense("by"), oninput: State.setlicense }),
                        m("label[for=license-by]", State.licensefullname("by")),
                        m("br"),
                        m("input[type=checkbox]#license-by-nc", { name: "licenses", value: "by-nc", checked: State.haslicense("by-nc"), oninput: State.setlicense }),
                        m("label[for=license-by-nc]", State.licensefullname("by-nc")),
                    ]),
                    m("button", { onclick: State.retrieve }, "Fetch pack"),
                    m("br"),
                    m("br"),
                    m("div.help", [
                        m("img", { src: "assets/help.png", height: "32", title: "Help" }),
                        m("p.explanation", [
                            "Any word can be a pack definition.",
                            m("br"),
                            "If you want more than one sample, separate words by a comma: blue,red",
                            m("br"),
                            m("br"),
                            "You can define how many variations of a sample to assemble by adding a colon and a number.",
                            m("br"),
                            "e.g. 'blue,red:3,yellow:2' will produce one 'blue' sample, three 'red' samples and two 'yellow' sample.",
                            m("br"),
                            m("br"),
                            "In a hurry? You can directly include a pack in Estuary by executing in its terminal:",
                            m("pre", '!reslist "' + location.href + 'blue,red.json"'),
                            "Or in Strudel:",
                            m("pre", "samples('shabda:blue:2,red:3')"),
                        ]),
                    ]),
                ]),

                m("div.clear"),

                m("div.tabcontent", { style: State.tab == "speech" ? "display:block;" : "" }, [
                    m("input[placeholder=Speech definition]#speechdefinition", {
                        value: State.speech,
                        oninput: function (e) { State.speech = e.target.value },
                        onkeyup: function (e) {
                            if (e.keyCode == 13) {
                                State.retrievespeech()
                            }
                        },
                    }),
                    m("div#genders", [
                        m("select#gender", { onchange: function () { State.speechGender = this.value } }, [
                            m("option[value=f]", { selected: State.speechGender == "f" }, "Female"),
                            m("option[value=m]", { selected: State.speechGender == "m" }, "Male"),
                        ]),
                    ]),
                    m("div#languages", [renderLanguageSelect("language", State.speechLanguage, function () { State.speechLanguage = this.value })]),
                    m("button", { onclick: State.retrievespeech }, "Fetch speech"),
                    m("br"),
                    m("br"),
                    m("div.help", [
                        m("img", { src: "assets/help.png", height: "32", title: "Help" }),
                        m("p.explanation", [
                            "Any word can be a speech definition.",
                            m("br"),
                            "If you want more than one sample, separate words by a comma: blue,red",
                            m("br"),
                            m("br"),
                            "You can use sentences by replacing spaces by underscores.",
                            m("br"),
                            "e.g. 'imagine_all,the_people' will produce a 'imagine all' sample and a 'the people' sample.",
                            m("br"),
                            m("br"),
                            "In a hurry? You can directly include speech in Estuary by executing in its terminal:",
                            m("pre", '!reslist "' + location.href + 'speech/blue,red.json?gender=f&language=en-GB"'),
                            "Or in Strudel:",
                            m("pre", "samples('shabda/speech/en-GB/f:blue,red')"),
                        ]),
                    ]),
                ]),

                m("div.tabcontent", { style: State.tab == "phonemes" ? "display:block;" : "" }, [
                    m("textarea[placeholder=Phoneme definition]#phonemedefinition", {
                        value: State.phonemes,
                        oninput: function (e) { State.phonemes = e.target.value },
                        onkeyup: function (e) {
                            if (e.keyCode == 13) {
                                State.retrievephonemes()
                            }
                        },
                    }),
                    m("div#timing", [
                        m("label", ["Beats / bar ", m("input[type=number]#beatsperbar", {
                            min: 1,
                            step: 1,
                            value: State.beatsPerBar,
                            oninput: function (e) { State.beatsPerBar = Number(e.target.value || 4) },
                        })]),
                        m("label", ["Bars / line ", m("input[type=number]#barsperline", {
                            min: 1,
                            step: 1,
                            value: State.barsPerLine,
                            oninput: function (e) { State.barsPerLine = Number(e.target.value || 2) },
                        })]),
                        m("label", ["Target stress beat ", m("input[type=number]#targetstressbeat", {
                            min: 1,
                            step: 1,
                            value: State.targetStressBeat,
                            oninput: function (e) { State.targetStressBeat = Number(e.target.value || 3) },
                        })]),
                    ]),
                    m("div#genders", [
                        m("select#gender-phonemes", { onchange: function () { State.phonemeGender = this.value } }, [
                            m("option[value=f]", { selected: State.phonemeGender == "f" }, "Female"),
                            m("option[value=m]", { selected: State.phonemeGender == "m" }, "Male"),
                        ]),
                    ]),
                    m("div#languages", [renderLanguageSelect("language-phonemes", State.phonemeLanguage, function () { State.phonemeLanguage = this.value })]),
                    m("div#overrides", [
                        m("label[for=phoneme-overrides]", "ARPABET overrides"),
                        m("input#phoneme-overrides[placeholder=word:PH1_PH2;other:PH1_PH2]", {
                            value: State.phonemeOverrides,
                            oninput: function (e) { State.phonemeOverrides = e.target.value },
                        }),
                    ]),
                    m("button", { onclick: function () { State.retrievephonemes(true) } }, "Preview phonemes"),
                    m("button", { onclick: function () { State.retrievephonemes(false) } }, "Generate audio banks"),
                    m("br"),
                    m("br"),
                    m("div.help", [
                        m("img", { src: "assets/help.png", height: "32", title: "Help" }),
                        m("p.explanation", [
                            "Phoneme samples stay separated by word, while stress still shapes the sample boundaries.",
                            m("br"),
                            "Beat settings control how the Strudel phrase is padded with rests so each sample starts on a beat.",
                            m("br"),
                            "Preview first to get the text output immediately; generate audio when you want the WAV banks.",
                            m("br"),
                            "The result shows IPA, ARPABET, Strudel chunks, and the generated audio banks.",
                            m("br"),
                            m("br"),
                            "In a hurry? You can directly include phonemes in Strudel by executing in its terminal:",
                            m("pre", "samples('shabda/phonemes/en-GB/f:hello_world')"),
                        ]),
                    ]),
                ]),

                m("div.pack-container", [
                    m("h2", State.lastretrievedtype == "phonemes" ? "Phonemes" : "Samples"),
                    m("div.pack",
                        State.error ? m("span.error", State.error) :
                            State.progress ?
                                m("img", { src: "assets/infinity.svg" }) :
                                State.lastretrieved ?
                                    State.lastretrievedtype == "phonemes" ?
                                        m("div.latest.phoneme-results", [
                                            renderCopyControls(),
                                            m("div.phoneme-sentences", (State.lastreslistcontents.sentences_phonetic || []).map(renderPhonemeSentence)),
                                            m("div.phoneme-strudel", [
                                                m("h3", "Timed Strudel lines"),
                                                m("pre", m("code", toQuotedStringList(flattenStringLists(State.lastreslistcontents.sentences_strudel_timed)))),
                                                m("h3", "Strudel chunks"),
                                                m("pre", m("code", toQuotedStringList(State.lastreslistcontents.sentences_strudel || []))),
                                            ]),
                                            m("div.phoneme-audio", [
                                                m("h3", "Generated audio"),
                                                phonemeBanks.length ? phonemeBanks.map(function (bank) {
                                                    return renderPhonemeBank(bank, State.lastreslistcontents[bank] || [])
                                                }) : [
                                                    m("p", "Preview mode does not synthesize audio banks yet."),
                                                    m("button", { onclick: function () { State.retrievephonemes(false) } }, "Generate audio banks"),
                                                ],
                                            ]),
                                        ]) :
                                        m("div.latest", [
                                            renderCopyControls(),
                                            m("ul.samples", State.lastreslistcontents.map(function (sound) {
                                                return m("li", [
                                                    m("audio", { controls: true, src: sound.url }),
                                                    " ",
                                                    m("span.attribution",
                                                        sound.licensename ? State.licensefullname(sound.licensename) + " by " + sound.author + " " : "",
                                                        sound.original_url ? m("a", { href: sound.original_url }, m("img", { src: "assets/external-link.png" })) : ""
                                                    )
                                                ])
                                            })),
                                            m("a.button", { href: State.lastretrievedzip() }, "Download all"),
                                        ]) :
                                    m("i", State.tab == "phonemes" ? "Fetch a definition to inspect its phonemes" : "Fetch a definition to hear its rendition")
                    )
                ]),
            ]),

            m("p.footer", [
                m("a", { href: "https://github.com/ilesinge/shabda", title: "Source code" }, m("img", { src: "assets/github.png", height: "16px" })),
                " by ",
                m("a", { href: "https://mastodon.sdf.org/@detour" }, "ilesinge"),
            ]),
        ])
    },
}

m.mount(root, Shabda)
State.pollStatus()
setInterval(State.pollStatus, 30000)
