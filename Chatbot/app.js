var restify = require('restify');
var builder = require('botbuilder');
var url = require('url');
var fs = require('fs');
var azure = require('botbuilder-azure');

var needle = require('needle'), //Speech-to-text
    ffmpeg = require('fluent-ffmpeg'),
    speechService = require('./speech-service.js');

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

//Setup Azure Table
var tableName = 'metisbot';
var azureTableClient = new azure.AzureTableClient(tableName,"metisbot","b9YdNPfchtxl2HhmrRXMBQhnOb3F0jci7VfjzDdbcfnbN9LuhM8Q87BVrO9f2tpu+ElXgm/V5iXw9e/Pj95Vvg==");
var tableStorage = new azure.AzureBotStorage({ gzipData: false }, azureTableClient);

// Initialize a bot
var bot = new builder.UniversalBot(connector).set('storage', tableStorage);;

// Listen for messages from users 
server.post('/api/messages', connector.listen());

// LUIS Natural Language Processing
var recognizer = new builder.LuisRecognizer("https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/0b06c54f-3ebf-4806-bc8b-da05908fc314?subscription-key=2c282b6ca94042ac891d9b66315517c3&staging=true&verbose=true&timezoneOffset=0&q=");
bot.recognizer(recognizer);

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
// Bots Middleware
//=========================================================

bot.use({
    botbuilder: function (session, next) {
        if (hasAudioAttachment(session)) {
            getAudioStreamFromMessage(session.message, function (stream) {
                speechService.getTextFromAudioStream(stream)
                    .then(function (text) {
                        session.message.text = text;
                        next();
                    })
                    .catch(function (error) {
                        console.error(error);
                        next();
                    });
            });
        } else {
            next();
        }
    }
});

//=========================================================
// Bot Start
//=========================================================

// Send welcome when conversation with bot is started, by initiating the root dialog
bot.on('conversationUpdate', function (message) {
    if (message.membersAdded) {
        message.membersAdded.forEach(function (identity) {
            if (identity.id === message.address.bot.id) {
                bot.beginDialog(message.address, '/');
            }
        });
    }
});

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

bot.dialog('Specs', function (session, args) {
    // retrieve hotel name from matched entities
    var deviceEntity = builder.EntityRecognizer.findEntity(args.intent.entities, 'device');
    if (deviceEntity) {
        session.send('Looking for specifications of \'%s\'...', deviceEntity.entity);
        session.endDialog('Dimensions: 11.5" x 7.9" x 0.33" (292 mm x 201 mm x 8.5 mm)\nDisplay	Screen: 12.3" PixelSense Display\nResolution: 2736 x 1824 (267 PPI)\nTouch: 10 point multi- touch\nMemory: 4GB, 8GB, or 16GB RAM\nProcessor: Intel Core 7th- generation m3, i5, or i7\nBattery Life: Up to 13.5 hours of video playback\nGraphics: Intel HD Graphics 615 (m3), Intel HD Graphics 620 (i5), Intel Iris Plus Graphics 640 (i7)');
    }
}).triggerAction({
    matches: 'Specs'
});

//=========================================================
// Utilities
//=========================================================

function hasAudioAttachment(session) {
    if (session.message.attachments) {
        return session.message.attachments.length > 0 &&
            (session.message.attachments[0].contentType === 'audio/wav' ||
                session.message.attachments[0].contentType === 'application/octet-stream' || session.message.attachments[0].contentType === 'audio/x-m4a' || session.message.attachments[0].contentType === 'audio/aac' || session.message.attachments[0].contentType === 'audio/vnd.dlna.adts');
    }
}


function getAudioStreamFromMessage(message, cb) {
    var headers = {};
    var attachment = message.attachments[0];
    if (checkRequiresToken(message)) {
        // The Skype attachment URLs are secured by JwtToken,
        // you should set the JwtToken of your bot as the authorization header for the GET request your bot initiates to fetch the image.
        // https://github.com/Microsoft/BotBuilder/issues/662
        connector.getAccessToken(function (error, token) {
            var tok = token;
            headers['Authorization'] = 'Bearer ' + token;
            headers['Content-Type'] = 'application/octet-stream';
        });
    }
    if (attachment.contentType === 'audio/x-m4a' || attachment.contentType === 'audio/aac' || attachment.contentType === 'audio/vnd.dlna.adts') {
        headers['Content-Type'] = attachment.contentType;
        var original = needle.get(attachment.contentUrl, { headers: headers, decode: false });
        original.on('finish', function () {
            var command = ffmpeg(original).toFormat('wav');
            var converted = command.pipe();
            command
                .on('error', function (err) {
                    console.log('An error occurred: ' + err.message);
                })
                .on('end', function () {
                    console.log('Processing finished !');
                    cb(converted);
                });
        });
    }
    else {
        headers['Content-Type'] = attachment.contentType;
        cb(needle.get(attachment.contentUrl, { headers: headers }));
    }
}

function checkRequiresToken(message) {
    return message.source === 'skype' || message.source === 'msteams';
}