# Trial one

Note that for questdb performance in this test, we ran into an issue between our benchmark setup and questdb config: 

We are running several runs of tsbs which writes the same data fields to the same timestamp several times, which works fine for the other databases in the benchmark, but chokes quest which expects data to be written mostly chronologically. This can be seen inspecting the run data in the questdb result files:

```json
"questdb_test_iot": {
    "rows": [
        725166.07,
        574021.55,
        36812.78,
        19646.64,
        46000.52
    ],
}
```

The more we write to the same place, the more it slows down. 
