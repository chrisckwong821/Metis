var sql = require('mssql');

var dbSettings = {
    server: process.env.DB_SERVER,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB,
    options: {
        encrypt: true // Use this if you're on Windows Azure
    }
};

/*
[
 {
     name: Item,
     value : 'waffles'
 },
 {
     name: Amount,
     value : 12.0
 },
 {
     name: UserId,
     value : 923
 }
]
 */
function insertTransaction(trObject) {
    var conn = new sql.Connection(dbSettings);
    conn.connect().then(function () {
        var transaction = new sql.Transaction(conn);
        transaction.begin().then(function () {
            var req = new sql.Request(transaction);

            //creating query string
            var qString = "Insert into Transactions(";
            trObject.forEach(function (item) {
                qString += item.name + ",";
            });
            qString = qString.slice(0, -1);
            qString += ") Values(";
            trObject.forEach(function (item) {
                qString += item.value.toString() + ",";
            });
            qString = qString.slice(0, -1);
            qString += ")";
            //console.log(qString);

            req.query(qString).then(function () {
                transaction.commit().then(function (recordSet, affected) {
                    console.log(affected);
                    conn.close();
                })
                    .catch(function (err) {
                        console.error("Error in committing: " + err);
                        conn.close();
                    });
            })
                .catch(function (err) {
                    console.error("Error in query: " + err);
                    conn.close();
                });
        })
            .catch(function (err) {
                console.error("Error in begin: " + err);
                conn.close();
            });
    })
        .catch(function (err) { console.error(err); });

}

function getReport(qrObj, callback) {
    var conn = new sql.Connection(dbSettings);
    var req = new sql.Request(conn);
    conn.connect().then(function () {
        var query = "Select * from Transactions where UserId='" + qrObj.userId + "'";
        if (qrObj.startDate) {
            query += " and DateandTime >= '" + qrObj.startDate + "'";
        }
        if (qrObj.endDate) {
            query += " and DateandTime < '" + qrObj.endDate + "'";
        }
        req.query(query).then(function (recordSet) {
            console.log(recordSet);
            callback(recordSet);
        })
            .catch(function (err) { console.error(err); conn.close(); });
    })
        .catch(function (err) { console.error(err); });

}

function getUser(userId, callback) {
    var conn = new sql.Connection(dbSettings);
    var req = new sql.Request(conn);
    conn.connect().then(function () {
        req.query("Select UserId from Users where UserId='" + userId + "'").then(function (recordSet) {
            console.log(recordSet);
            callback(recordSet);
        })
            .catch(function (err) { console.error(err); conn.close(); });
    })
        .catch(function (err) { console.error(err); });

}

function insertNewUser(usrObj) {
    var conn = new sql.Connection(dbSettings);
    conn.connect().then(function () {
        var transaction = new sql.Transaction(conn);
        transaction.begin().then(function () {
            var req = new sql.Request(transaction);
            req.query("insert into Users(UserId, UserName) Values('" + usrObj.id + "','" + usrObj.name + "')").then(function () {
                transaction.commit().then(function (recordSet, affected) {
                    console.log(affected);
                    conn.close();
                })
                    .catch(function (err) {
                        console.error("Error in committing: " + err);
                        conn.close();
                    });
            })
                .catch(function (err) {
                    console.error("Error in query: " + err);
                    conn.close();
                });
        })
            .catch(function (err) {
                console.error("Error in begin: " + err);
                conn.close();
            });
    })
        .catch(function (err) { console.error(err); });

}


module.exports.insertTr = insertTransaction;
module.exports.getReport = getReport;
module.exports.getUser = getUser;
module.exports.newUser = insertNewUser;