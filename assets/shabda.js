var root = document.body

var State = {
    pack: "",
    progress: false,
    lastretrieved: "",
    lastreslistcontents: [],
    error: "",
    licenses: ["by", "cc0", "by-nc"],

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

    lastreslist: function () {
        return '!reslist "' + location.href + State.lastretrievedreslist() + (State.licenses.length < 3 ? "?licenses=" + State.licenses.join() : "") + '"'
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
    copyreslist: function () {
        if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
            if (navigator.clipboard.writeText(State.lastreslist())) {
                State.copied = true
            }
        }
        setTimeout(function () {
            State.copied = false
            m.redraw()
        }, 2000)
    }
}

var Shabda = {
    view: function () {
        return m("main", [
            m("h1", [m("img", { src: "assets/logo.svg", height: "40", title: 'Shabda is the Sanskrit word for "speech sound"' }), "Shabda"]),

            m("p.intro", ["Shabda is a tool for assembling and sharing packs of found audio samples.",
                m("br"),
                "It fetches samples from ",
                m("a", { href: "https://freesound.org/" }, "freesound.org"),
                " based on given words, for use in impro sessions on instruments such as ",
                m("a", { href: "https://tidalcycles.org/" }, "Tidal Cycles"),
                " and ",
                m("a", { href: "https://estuary.mcmaster.ca/" }, "Estuary"),
                "."]),

            m("div",
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
                        m("pre", '!reslist "' + location.href + 'blue,red.json"')
                    ]),
                ]),

                m("div.pack-container", [
                    m("h2", "Pack"),
                    m("div.pack",
                        State.error ? m("span.error", State.error) :
                            State.progress ?
                                m("img", { src: "assets/infinity.svg" }) :
                                State.lastretrieved ?
                                    m("div.latest", [
                                        "Insert in Estuary terminal: ",
                                        m("br"),
                                        m("pre", State.lastreslist()),
                                        m("img", { onclick: State.copyreslist, src: "assets/clipboard.png", height: "16" }),
                                        State.copied ? m("span.copied", "copied") : null,
                                        m('ul.samples', function () {
                                            soundlist = []
                                            for (index in State.lastreslistcontents) {
                                                sound = State.lastreslistcontents[index]
                                                soundlist.push(m('li', m('audio', { controls: true, src: sound.url }), " ", m('span.attribution', State.licensefullname(sound.licensename) + ' by ' + sound.author + ' ', m('a', { 'href': sound.original_url }, m('img', { src: 'assets/external-link.png' })))))
                                            }
                                            return soundlist
                                        }()),
                                        m("a.button", { href: State.lastretrievedzip() }, "Download all"),
                                    ]) :
                                    m("i", "Fetch a pack to see its contents")
                    )
                ]),
            ),

            m('p.footer',
                [
                    m('a', { href: "https://github.com/ilesinge/shabda", title: "Source code" }, m('img', { src: "assets/github.png", height: "16px" })),
                    ' by ',
                    m('a', { href: "https://twitter.com/ilesinge" }, 'ilesinge')
                ]
            )
        ])
    }
}
m.mount(root, Shabda)