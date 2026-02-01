var root = document.body

var State = {
    pack: "",
    progress: false,
    lastretrievedtype: "",
    lastretrieved: "",
    lastreslistcontents: [],
    error: "",
    licenses: ["by", "cc0", "by-nc"],
    speech: "",
    language: "uk-UA",
    gender: "f",
    tab: "pack",

    licensefullname: function (name) {
        switch (name) {
            case 'cc0': return "Public domain"
            case 'by': return "Attribution"
            case 'by-nc': return "Attribution non-commercial"
        }
    },

    haslicense: function (name) {
        return State.licenses.includes(name)
    },

    setlicense: function (e) {
        name = e.target.value
        if (State.licenses.includes(name)) {
            State.licenses = State.licenses.filter(function (value, index, arr) {
                return value != name;
            });
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
        url = new URL(location.href + State.lastretrievedreslist())
        if (this.lastretrievedtype == "pack" && State.licenses.length < 3) {
            url.searchParams.append("licenses", State.licenses.join());
        }
        if (this.lastretrievedtype == "speech") {
            url.searchParams.append("gender", State.gender)
            url.searchParams.append("language", State.language)
        }
        if (strudel) {
            url.searchParams.append("strudel", 1)
            reslist = "samples('" + url.href + "')"
        }
        else {
            reslist = '!reslist "' + url.href + '"'
        }

        return reslist
    },

    retrieve: function () {
        if (State.pack) {
            State.error = ""
            State.progress = true
            m.request({
                method: "GET",
                url: "/pack/" + encodeURIComponent(State.pack) + '?licenses=' + State.licenses.join()
            })
                .then(function (result) {
                    State.progress = false
                    if (result.status == "ok") {
                        State.lastretrieved = result.definition
                        State.lastretrievedtype = "pack"
                        m.request({
                            method: "GET",
                            url: encodeURIComponent(State.lastretrievedreslist()) + '?complete=1&licenses=' + State.licenses.join()
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
                }).catch(function (error) {
                    State.error = "An error occured"
                })
        }
        else {
            State.error = "Please enter a pack definition"
        }
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
        if (State.speech) {
            State.error = ""
            State.progress = true
            m.request({
                method: "GET",
                url: "/speech/" + encodeURIComponent(State.speech) + '?language=' + State.language + '&gender=' + State.gender
            })
                .then(function (result) {
                    State.progress = false
                    if (result.status == "ok") {
                        State.lastretrieved = "speech/" + result.definition
                        State.lastretrievedtype = "speech"
                        m.request({
                            method: "GET",
                            url: encodeURIComponent(State.lastretrievedreslist()) + '?language=' + State.language + '&gender=' + State.gender
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
                }).catch(function (error) {
                    State.error = "An error occured"
                })
        }
        else {
            State.error = "Please enter a pack definition"
        }
    },
}

var Shabda = {
    view: function () {
        return m("main", [
            m("h1", [m("img", { src: "assets/logo.svg", height: "40", title: 'Shabda is the Sanskrit word for "speech sound"' }), "Shabda"]),

            m("p.intro", ["Shabda is a tool for assembling and sharing packs of found audio samples.",
                m("br"),
                "It fetches samples from ",
                m("a", { href: "https://freesound.org/" }, "freesound.org"),
                " based on given words or generates Text-to-Speech samples, for use in impro sessions on instruments such as ",
                m("a", { href: "https://tidalcycles.org/" }, "Tidal Cycles"),
                ", ",
                m("a", { href: "https://estuary.mcmaster.ca/" }, "Estuary"),
                " and ",
                m("a", { href: "https://strudel.tidalcycles.org/" }, "Strudel"),
                "."]),

            m("div",
                m("div#tabs", [
                    m("span#packs_tab",
                        {
                            class: State.tab == "pack" ? "selected" : "",
                            onclick: function () { State.tab = "pack" }
                        },
                        "Pack"
                    ),
                    m("span#speech_tab",
                        {
                            class: State.tab == "speech" ? "selected" : "",
                            onclick: function () { State.tab = "speech" }
                        },
                        "Speech"
                    ),
                ]),
                m("div.tabcontent", { style: State.tab == "pack" ? "display:block;" : "" }, [
                    m("input[placeholder=Pack definition]#definition", {
                        value: State.pack,
                        oninput: function (e) { State.pack = e.target.value },
                        onkeyup: function (e) {
                            if (e.keyCode == 13) {
                                State.retrieve()
                            }
                        }
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
                    m("button", {
                        onclick: State.retrieve
                    }, "Fetch pack"),

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
                            m("pre", "samples('shabda:blue:2,red:3')")
                        ]),
                    ])
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
                        }
                    }),
                    m("div#genders", [
                        m("select#gender", { onchange: function (e) { State.gender = this.value } }, [
                            m("option[value=f]", { selected: State.gender == "f" }, "Female"),
                            m("option[value=m]", { selected: State.gender == "m" }, "Male")
                        ]),
                    ]),
                    m("div#languages", [
                        m('select#language', { onchange: function (e) { State.language = this.value }, value: State.language }, [
                            m("option[value=af-ZA]", "Afrikaans"),
                            m("option[value=ar-XA]", "Arabic"),
                            m("option[value=bn-IN]", "Bengali"),
                            m("option[value=bg-BG]", "Bulgarian"),
                            m("option[value=ca-ES]", "Catalan"),
                            m("option[value=yue-HK]", "Chinese (Hong Kong)"),
                            m("option[value=cs-CZ]", "Czech"),
                            m("option[value=da-DK]", "Danish"),
                            m("option[value=nl-BE]", "Dutch (Belgium)"),
                            m("option[value=nl-NL]", "Dutch (Netherlands)"),
                            m("option[value=en-AU]", "English (Australia)"),
                            m("option[value=en-IN]", "English (India)"),
                            m("option[value=en-GB]", "English (UK)"),
                            m("option[value=en-US]", "English (US)"),
                            m("option[value=fil-PH]", "Filipino"),
                            m("option[value=fi-FI]", "Finnish"),
                            m("option[value=fr-CA]", "French (Canada)"),
                            m("option[value=fr-FR]", "French (France)"),
                            m("option[value=de-DE]", "German"),
                            m("option[value=el-GR]", "Greek"),
                            m("option[value=gu-IN]", "Gujarati"),
                            m("option[value=hi-IN]", "Hindi"),
                            m("option[value=hu-HU]", "Hungarian"),
                            m("option[value=is-IS]", "Icelandic"),
                            m("option[value=id-ID]", "Indonesian"),
                            m("option[value=it-IT]", "Italian"),
                            m("option[value=ja-JP]", "Japanese"),
                            m("option[value=kn-IN]", "Kannada"),
                            m("option[value=ko-KR]", "Korean"),
                            m("option[value=lv-LV]", "Latvian"),
                            m("option[value=ms-MY]", "Malay"),
                            m("option[value=ml-IN]", "Malayalam"),
                            m("option[value=cmn-CN]", "Mandarin Chinese"),
                            m("option[value=mr-IN]", "Marathi"),
                            m("option[value=nb-NO]", "Norwegian"),
                            m("option[value=pl-PL]", "Polish"),
                            m("option[value=pt-BR]", "Portuguese (Brazil)"),
                            m("option[value=pt-PT]", "Portuguese (Portugal)"),
                            m("option[value=pa-IN]", "Punjabi"),
                            m("option[value=ro-RO]", "Romanian"),
                            m("option[value=ru-RU]", "Russian"),
                            m("option[value=sr-RS]", "Serbian"),
                            m("option[value=sk-SK]", "Slovak"),
                            m("option[value=es-ES]", "Spanish (Spain)"),
                            m("option[value=es-US]", "Spanish (US)"),
                            m("option[value=sv-SE]", "Swedish"),
                            m("option[value=ta-IN]", "Tamil"),
                            m("option[value=te-IN]", "Telugu"),
                            m("option[value=th-TH]", "Thai"),
                            m("option[value=tr-TR]", "Turkish"),
                            m("option[value=uk-UA]", "Ukrainian"),
                            m("option[value=vi-VN]", "Vietnamese")
                        ])
                    ]),
                    m("button", {
                        onclick: State.retrievespeech
                    }, "Fetch speech"),

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
                            m("pre", "samples('shabda/speech/en-GB/f:blue,red')")
                        ]),
                    ])
                ]),

                m("div.pack-container", [
                    m("h2", "Samples"),
                    m("div.pack",
                        State.error ? m("span.error", State.error) :
                            State.progress ?
                                m("img", { src: "assets/infinity.svg" }) :
                                State.lastretrieved ?
                                    m("div.latest", [
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
                                        m('ul.samples', function () {
                                            soundlist = []
                                            for (index in State.lastreslistcontents) {
                                                sound = State.lastreslistcontents[index]
                                                soundlist.push(
                                                    m('li',
                                                        m('audio', { controls: true, src: sound.url }),
                                                        " ",
                                                        m('span.attribution',
                                                            sound.licensename ? State.licensefullname(sound.licensename) + ' by ' + sound.author + ' ' : '',
                                                            sound.original_url ? m('a', { 'href': sound.original_url }, m('img', { src: 'assets/external-link.png' })) : ''
                                                        )
                                                    )
                                                )
                                            }
                                            return soundlist
                                        }()),
                                        m("a.button", { href: State.lastretrievedzip() }, "Download all"),
                                    ]) :
                                    m("i", "Fetch a definition to hear its rendition")
                    )
                ]),
            ),

            m('p.footer',
                [
                    m('a', { href: "https://github.com/ilesinge/shabda", title: "Source code" }, m('img', { src: "assets/github.png", height: "16px" })),
                    ' by ',
                    m('a', { href: "https://mastodon.sdf.org/@detour" }, 'ilesinge')
                ]
            )
        ])
    }
}
m.mount(root, Shabda)
