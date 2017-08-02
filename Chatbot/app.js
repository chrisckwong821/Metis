var restify = require('restify');
var builder = require('botbuilder');
var url = require('url');
fs = require('fs');

// Setup Restify Server
var server = restify.createServer();
server.listen(/*|| process.env.port || process.env.PORT ||*/ 3978, function () {
    console.log('%s listening to %s', server.name, server.url);
});

// Create chat connector for communicating with the Bot Framework Service
var connector = new builder.ChatConnector({
    appId: process.env.MICROSOFT_APP_ID,
    appPassword: process.env.MICROSOFT_APP_PASSWORD
});

// Initialize a bot
var bot = new builder.UniversalBot(connector);

// Listen for messages from users 
server.post('/api/messages', connector.listen());

//=========================================================
// Bots Global Actions
//=========================================================

bot.endConversationAction('goodbye', 'Goodbye :)', { matches: /^goodbye/i });
bot.beginDialogAction('help', '/help', { matches: /^help/i });
bot.beginDialogAction('reset', '/reset', { matches: /^reset/i });

//=========================================================
// Listener
//=========================================================
// Do GET this endpoint to start a dialog proactively
server.get('/api/listener', function (req, res, next) {
    var query = url.parse(req.url, true).query;
    fs.readFile("file.bin", (err, data) => {
        if (err) console.log(err)
        else {
            var savedAddresses = { '123112': JSON.parse(data) };
            var customerAddress = savedAddresses[query.customerid];
            startProactiveDialog(customerAddress);
            res.send('triggered');
            next();
        }
    })
});

// initiate a dialog proactively 
function startProactiveDialog(address) {
    bot.beginDialog(address, "*:/WelcomeExistingCustomer");
}

//=========================================================
// Bots Dialogs
//=========================================================

// Receive messages from the user and respond by echoing each message back (prefixed with 'You said:')
bot.dialog('/', function (session) {
    fs.writeFile("file.bin", JSON.stringify(session.message.address), 'binary', (err) => {
        if (err) console.log(err)
        else console.log('File saved')
    })
    session.endConversation("You said: %s", session.message.text);
});

// handle the proactive initiated dialog
bot.dialog('/WelcomeExistingCustomer', function (session, args, next) {
        session.endDialog('Hello %s, Welcome to the store!',session.message.user.name);
});