import {Command, Session} from "../session";
import {CommandHandler} from "./base";
import {GetPinValue, PinChangeCallback, PinUpdate, WaitChange} from "../models/pin";
import {state} from "../state";


export class PinHandler implements CommandHandler {
    session: Session;

    accept_command = ['pin_value', 'pin_update', 'pin_wait', 'pin_onchange'];

    constructor(session: Session) {
        this.session = session;
    }

    handle_message(msg: Command) {
        if (msg.command === 'pin_value') {
            let val = GetPinValue(msg.spec.name);
            let data = val===undefined? null : {value: val};
            state.CurrentSession.send_message({event: "js_yield", task_id: msg.task_id, data: data});
        } else if (msg.command === 'pin_update') {
            PinUpdate(msg.spec.name, msg.spec.attributes);
        } else if (msg.command === 'pin_wait') {
            let p = WaitChange(msg.spec.names, msg.spec.timeout);
            Promise.resolve(p).then(function (value) {
                state.CurrentSession.send_message({event: "js_yield", task_id: msg.task_id, data: value});
            }).catch((error) => {
                console.error('error in `pin_wait`: %s', error);
                state.CurrentSession.send_message({event: "js_yield", task_id: msg.task_id, data: null});
            });
        }else if (msg.command === 'pin_onchange') {
            PinChangeCallback(msg.spec.name, msg.spec.callback_id, msg.spec.clear);
        }

    }
}