import { createRouter, createWebHistory} from "vue-router"

import Main from "../views/Main.vue"
import Admin from "../views/Admin.vue"

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),

    routes:[
        {
            path:"/",
            name:"main",
            component:Main
        },
        {
            path:"/admin",
            name:"admin",
            component:Admin
        }
    ]
})

export default router
